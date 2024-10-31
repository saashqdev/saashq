# Copyright (c) 2022, Saashq Technologies and contributors
# For license information, please see license.txt


import saashq
from saashq import _
from saashq.core.doctype.doctype.doctype import validate_series
from saashq.model.document import Document
from saashq.model.naming import NamingSeries
from saashq.permissions import get_doctypes_with_read


class NamingSeriesNotSetError(saashq.ValidationError):
	pass


class DocumentNamingSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.core.doctype.amended_document_naming_settings.amended_document_naming_settings import (
			AmendedDocumentNamingSettings,
		)
		from saashq.types import DF

		amend_naming_override: DF.Table[AmendedDocumentNamingSettings]
		current_value: DF.Int
		default_amend_naming: DF.Literal["Amend Counter", "Default Naming"]
		naming_series_options: DF.Text | None
		prefix: DF.Autocomplete | None
		series_preview: DF.Text | None
		transaction_type: DF.Autocomplete | None
		try_naming_series: DF.Data | None
		user_must_always_select: DF.Check
	# end: auto-generated types

	@saashq.whitelist()
	def get_transactions_and_prefixes(self):
		transactions = self._get_transactions()
		prefixes = self._get_prefixes(transactions)

		return {"transactions": transactions, "prefixes": prefixes}

	def _get_transactions(self) -> list[str]:
		readable_doctypes = set(get_doctypes_with_read())

		standard = saashq.get_all("DocField", {"fieldname": "naming_series"}, "parent", pluck="parent")
		custom = saashq.get_all("Custom Field", {"fieldname": "naming_series"}, "dt", pluck="dt")

		return sorted(readable_doctypes.intersection(standard + custom))

	def _get_prefixes(self, doctypes) -> list[str]:
		"""Get all prefixes for naming series.

		- For all templates prefix is evaluated considering today's date
		- All existing prefix in DB are shared as is.
		"""
		series_templates = set()
		for d in doctypes:
			try:
				options = saashq.get_meta(d).get_naming_series_options()
				series_templates.update(options)
			except saashq.DoesNotExistError:
				saashq.msgprint(_("Unable to find DocType {0}").format(d))
				continue

		custom_templates = saashq.get_all(
			"DocType",
			fields=["autoname"],
			filters={
				"name": ("not in", doctypes),
				"autoname": ("like", "%.#%"),
				"module": ("not in", ["Core"]),
			},
		)
		if custom_templates:
			series_templates.update([d.autoname.rsplit(".", 1)[0] for d in custom_templates])

		return self._evaluate_and_clean_templates(series_templates)

	def _evaluate_and_clean_templates(self, series_templates: set[str]) -> list[str]:
		evalauted_prefix = set()

		series = saashq.qb.DocType("Series")
		prefixes_from_db = saashq.qb.from_(series).select(series.name).run(pluck=True)
		evalauted_prefix.update(prefixes_from_db)

		for series_template in series_templates:
			try:
				prefix = NamingSeries(series_template).get_prefix()
				if "{" in prefix:
					# fieldnames can't be evalauted, rely on data in DB instead
					continue
				evalauted_prefix.add(prefix)
			except Exception:
				saashq.clear_last_message()
				saashq.log_error(f"Invalid naming series {series_template}")

		return sorted(evalauted_prefix)

	def get_options_list(self, options: str) -> list[str]:
		return [op.strip() for op in options.split("\n") if op.strip()]

	@saashq.whitelist()
	def update_series(self):
		"""update series list"""
		self.validate_set_series()
		self.check_duplicate()
		self.set_series_options_in_meta(self.transaction_type, self.naming_series_options)

		saashq.msgprint(
			_("Series Updated for {}").format(self.transaction_type), alert=True, indicator="green"
		)

	def validate_set_series(self):
		if self.transaction_type and not self.naming_series_options:
			saashq.throw(_("Please set the series to be used."))

	def set_series_options_in_meta(self, doctype: str, options: str) -> None:
		options = self.get_options_list(options)

		# validate names
		for series in options:
			self.validate_series_name(series)

		if options and self.user_must_always_select:
			options = ["", *options]

		default = options[0] if options else ""

		option_string = "\n".join(options)

		# Erase default first, it might not be in new options.
		self.update_naming_series_property_setter(doctype, "default", "")
		self.update_naming_series_property_setter(doctype, "options", option_string)
		self.update_naming_series_property_setter(doctype, "default", default)

		self.naming_series_options = option_string

		saashq.clear_cache(doctype=doctype)

	def update_naming_series_property_setter(self, doctype, property, value):
		from saashq.custom.doctype.property_setter.property_setter import make_property_setter

		make_property_setter(doctype, "naming_series", property, value, "Text")

	def check_duplicate(self):
		def stripped_series(s: str) -> str:
			return s.strip().rstrip("#")

		standard = saashq.get_all("DocField", {"fieldname": "naming_series"}, "parent", pluck="parent")
		custom = saashq.get_all("Custom Field", {"fieldname": "naming_series"}, "dt", pluck="dt")

		all_doctypes_with_naming_series = set(standard + custom)
		all_doctypes_with_naming_series.remove(self.transaction_type)

		existing_series = {}
		for doctype in all_doctypes_with_naming_series:
			for series in saashq.get_meta(doctype).get_naming_series_options():
				existing_series[stripped_series(series)] = doctype

		dt = saashq.get_doc("DocType", self.transaction_type)

		options = self.get_options_list(self.naming_series_options)
		for series in options:
			if stripped_series(series) in existing_series:
				saashq.throw(_("Series {0} already used in {1}").format(series, existing_series[series]))
			validate_series(dt, series)

	def validate_series_name(self, series):
		NamingSeries(series).validate()

	@saashq.whitelist()
	def get_options(self, doctype=None):
		doctype = doctype or self.transaction_type
		if not doctype:
			return

		if saashq.get_meta(doctype or self.transaction_type).get_field("naming_series"):
			return saashq.get_meta(doctype or self.transaction_type).get_field("naming_series").options

	@saashq.whitelist()
	def get_current(self):
		"""get series current"""
		if self.prefix is not None:
			self.current_value = NamingSeries(self.prefix).get_current_value()
		return self.current_value

	@saashq.whitelist()
	def update_amendment_rule(self):
		self.db_set("default_amend_naming", self.default_amend_naming)

		existing_overrides = saashq.db.get_all(
			"Amended Document Naming Settings",
			filters={"name": ["not in", [d.name for d in self.amend_naming_override]]},
			pluck="name",
		)
		for override in existing_overrides:
			saashq.delete_doc("Amended Document Naming Settings", override)

		for row in self.amend_naming_override:
			row.save()

		saashq.msgprint(_("Amendment naming rules updated."), indicator="green", alert=True)

	@saashq.whitelist()
	def update_series_start(self):
		saashq.only_for("System Manager")

		if self.prefix is None:
			saashq.throw(_("Please select prefix first"))

		naming_series = NamingSeries(self.prefix)
		previous_value = naming_series.get_current_value()
		naming_series.update_counter(self.current_value)

		self.create_version_log_for_change(naming_series.get_prefix(), previous_value, self.current_value)

		saashq.msgprint(
			_("Series counter for {} updated to {} successfully").format(self.prefix, self.current_value),
			alert=True,
			indicator="green",
		)

	def create_version_log_for_change(self, series, old, new):
		version = saashq.new_doc("Version")
		version.ref_doctype = "Series"
		version.docname = series or ".#"
		version.data = saashq.as_json({"changed": [["current", old, new]]})
		version.flags.ignore_links = True  # series is not a "real" doctype
		version.flags.ignore_permissions = True
		version.insert()

	@saashq.whitelist()
	def preview_series(self) -> str:
		"""Preview what the naming series will generate."""

		series = self.try_naming_series
		if not series:
			return ""
		try:
			doc = self._fetch_last_doc_if_available()
			return "\n".join(NamingSeries(series).get_preview(doc=doc))
		except Exception as e:
			saashq.clear_last_message()
			return _("Failed to generate names from the series") + f"\n{e!s}"

	def _fetch_last_doc_if_available(self):
		"""Fetch last doc for evaluating naming series with fields."""
		try:
			return saashq.get_last_doc(self.transaction_type)
		except Exception:
			return None
