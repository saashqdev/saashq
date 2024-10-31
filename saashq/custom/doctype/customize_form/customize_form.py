# Copyleft (l) 2023-Present, SaasHQ
# MIT License. See LICENSE

"""
	Customize Form is a Single DocType used to mask the Property Setter
	Thus providing a better UI from user perspective
"""
import json

import saashq
import saashq.translate
from saashq import _
from saashq.core.doctype.doctype.doctype import (
	check_email_append_to,
	validate_autoincrement_autoname,
	validate_fields_for_doctype,
	validate_series,
)
from saashq.custom.doctype.custom_field.custom_field import create_custom_field
from saashq.custom.doctype.property_setter.property_setter import delete_property_setter
from saashq.model import core_doctypes_list, no_value_fields
from saashq.model.docfield import supports_translation
from saashq.model.document import Document
from saashq.model.meta import trim_table
from saashq.utils import cint


class CustomizeForm(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.core.doctype.doctype_action.doctype_action import DocTypeAction
		from saashq.core.doctype.doctype_link.doctype_link import DocTypeLink
		from saashq.core.doctype.doctype_state.doctype_state import DocTypeState
		from saashq.custom.doctype.customize_form_field.customize_form_field import CustomizeFormField
		from saashq.types import DF

		actions: DF.Table[DocTypeAction]
		allow_auto_repeat: DF.Check
		allow_copy: DF.Check
		allow_import: DF.Check
		autoname: DF.Data | None
		default_email_template: DF.Link | None
		default_print_format: DF.Link | None
		default_view: DF.Literal[None]
		doc_type: DF.Link | None
		editable_grid: DF.Check
		email_append_to: DF.Check
		fields: DF.Table[CustomizeFormField]
		force_re_route_to_default_view: DF.Check
		image_field: DF.Data | None
		is_calendar_and_gantt: DF.Check
		istable: DF.Check
		label: DF.Data | None
		link_filters: DF.JSON | None
		links: DF.Table[DocTypeLink]
		make_attachments_public: DF.Check
		max_attachments: DF.Int
		naming_rule: DF.Literal[
			"",
			"Set by user",
			"By fieldname",
			'By "Naming Series" field',
			"Expression",
			"Expression (old style)",
			"Random",
			"By script",
		]
		queue_in_background: DF.Check
		quick_entry: DF.Check
		search_fields: DF.Data | None
		sender_field: DF.Data | None
		sender_name_field: DF.Data | None
		show_preview_popup: DF.Check
		show_title_field_in_link: DF.Check
		sort_field: DF.Literal[None]
		sort_order: DF.Literal["ASC", "DESC"]
		states: DF.Table[DocTypeState]
		subject_field: DF.Data | None
		title_field: DF.Data | None
		track_changes: DF.Check
		track_views: DF.Check
		translated_doctype: DF.Check
	# end: auto-generated types

	def on_update(self):
		saashq.db.delete("Singles", {"doctype": "Customize Form"})
		saashq.db.delete("Customize Form Field")

	@saashq.whitelist()
	def fetch_to_customize(self):
		self.clear_existing_doc()
		if not self.doc_type:
			return

		meta = saashq.get_meta(self.doc_type, cached=False)

		self.validate_doctype(meta)

		# load the meta properties on the customize (self) object
		self.load_properties(meta)

		# load custom translation
		translation = self.get_name_translation()
		self.label = translation.translated_text if translation else ""

		self.create_auto_repeat_custom_field_if_required(meta)

		# NOTE doc (self) is sent to clientside by run_method

	def validate_doctype(self, meta):
		"""
		Check if the doctype is allowed to be customized.
		"""
		if self.doc_type in core_doctypes_list:
			saashq.throw(_("Core DocTypes cannot be customized."))

		if meta.issingle:
			saashq.throw(_("Single DocTypes cannot be customized."))

		if meta.custom:
			saashq.throw(_("Only standard DocTypes are allowed to be customized from Customize Form."))

	def load_properties(self, meta):
		"""
		Load the customize object (this) with the metadata properties
		"""
		# doctype properties
		for prop in doctype_properties:
			self.set(prop, meta.get(prop))

		for d in meta.get("fields"):
			new_d = {
				"fieldname": d.fieldname,
				"is_custom_field": d.get("is_custom_field"),
				"is_system_generated": d.get("is_system_generated"),
				"name": d.name,
			}
			for prop in docfield_properties:
				new_d[prop] = d.get(prop)
			self.append("fields", new_d)

		for fieldname in ("links", "actions", "states"):
			for d in meta.get(fieldname):
				self.append(fieldname, d)

	def create_auto_repeat_custom_field_if_required(self, meta):
		"""
		Create auto repeat custom field if it's not already present
		"""
		if self.allow_auto_repeat:
			all_fields = [df.fieldname for df in meta.fields]

			if "auto_repeat" in all_fields:
				return

			insert_after = self.fields[len(self.fields) - 1].fieldname
			create_custom_field(
				self.doc_type,
				dict(
					fieldname="auto_repeat",
					label="Auto Repeat",
					fieldtype="Link",
					options="Auto Repeat",
					insert_after=insert_after,
					read_only=1,
					no_copy=1,
					print_hide=1,
				),
			)

	def get_name_translation(self):
		"""Get translation object if exists of current doctype name in the default language"""
		return saashq.get_value(
			"Translation",
			{"source_text": self.doc_type, "language": saashq.local.lang or "en"},
			["name", "translated_text"],
			as_dict=True,
		)

	def set_name_translation(self):
		"""Create, update custom translation for this doctype"""
		current = self.get_name_translation()
		if not self.label:
			if current:
				# clear translation
				saashq.delete_doc("Translation", current.name)
			return

		if not current:
			saashq.get_doc(
				{
					"doctype": "Translation",
					"source_text": self.doc_type,
					"translated_text": self.label,
					"language_code": saashq.local.lang or "en",
				}
			).insert()
			return

		if self.label != current.translated_text:
			saashq.db.set_value("Translation", current.name, "translated_text", self.label)
			saashq.translate.clear_cache()

	def clear_existing_doc(self):
		doc_type = self.doc_type

		for fieldname in self.meta.get_valid_columns():
			self.set(fieldname, None)

		for df in self.meta.get_table_fields():
			self.set(df.fieldname, [])

		self.doc_type = doc_type
		self.name = "Customize Form"

	@saashq.whitelist()
	def save_customization(self):
		if not self.doc_type:
			return

		validate_series(self, self.autoname, self.doc_type)
		validate_autoincrement_autoname(self)
		self.flags.update_db = False
		self.flags.rebuild_doctype_for_global_search = False
		self.update_custom_fields()
		self.set_property_setters()
		self.set_name_translation()
		validate_fields_for_doctype(self.doc_type)
		check_email_append_to(self)

		if self.flags.update_db:
			try:
				saashq.db.updatedb(self.doc_type)
			except Exception as e:
				if saashq.db.is_db_table_size_limit(e):
					saashq.throw(
						_("You have hit the row size limit on database table: {0}").format(
							"<a href='https://docs.erpnexus.com/docs/v14/user/manual/en/customize-erpnexus/articles/maximum-number-of-fields-in-a-form'>"
							"Maximum Number of Fields in a Form</a>"
						),
						title=_("Database Table Row Size Limit"),
					)
				raise

		if not hasattr(self, "hide_success") or not self.hide_success:
			saashq.msgprint(_("{0} updated").format(_(self.doc_type)), alert=True)
		saashq.clear_cache(doctype=self.doc_type)
		self.fetch_to_customize()

		if self.flags.rebuild_doctype_for_global_search:
			saashq.enqueue(
				"saashq.utils.global_search.rebuild_for_doctype",
				doctype=self.doc_type,
				enqueue_after_commit=True,
			)

	def set_property_setters(self):
		meta = saashq.get_meta(self.doc_type)

		# doctype
		self.set_property_setters_for_doctype(meta)

		# docfield
		for df in self.get("fields"):
			meta_df = meta.get("fields", {"fieldname": df.fieldname})
			if not meta_df or not is_standard_or_system_generated_field(meta_df[0]):
				continue

			self.set_property_setters_for_docfield(meta, df, meta_df)

		# action and links
		self.set_property_setters_for_actions_and_links(meta)

	def set_property_setter_for_field_order(self, meta):
		new_order = [df.fieldname for df in self.fields]
		existing_order = getattr(meta, "field_order", None)
		default_order = [
			fieldname for fieldname, df in meta._fields.items() if not getattr(df, "is_custom_field", False)
		]

		if new_order == default_order:
			if existing_order:
				delete_property_setter(self.doc_type, "field_order")

			return

		if existing_order and new_order == json.loads(existing_order):
			return

		saashq.make_property_setter(
			{
				"doctype": self.doc_type,
				"doctype_or_field": "DocType",
				"property": "field_order",
				"value": json.dumps(new_order),
			},
			is_system_generated=False,
		)

	def set_property_setters_for_doctype(self, meta):
		for prop, prop_type in doctype_properties.items():
			if self.get(prop) != meta.get(prop):
				self.make_property_setter(prop, self.get(prop), prop_type)

		self.set_property_setter_for_field_order(meta)

	def set_property_setters_for_docfield(self, meta, df, meta_df):
		for prop, prop_type in docfield_properties.items():
			if prop != "idx" and (df.get(prop) or "") != (meta_df[0].get(prop) or ""):
				if not self.allow_property_change(prop, meta_df, df):
					continue

				self.make_property_setter(prop, df.get(prop), prop_type, fieldname=df.fieldname)

	def allow_property_change(self, prop, meta_df, df):
		if prop == "fieldtype":
			self.validate_fieldtype_change(df, meta_df[0].get(prop), df.get(prop))

		elif prop == "length":
			old_value_length = cint(meta_df[0].get(prop))
			new_value_length = cint(df.get(prop))

			if new_value_length and (old_value_length > new_value_length):
				self.check_length_for_fieldtypes.append({"df": df, "old_value": meta_df[0].get(prop)})
				self.validate_fieldtype_length()
			else:
				self.flags.update_db = True

		elif prop == "allow_on_submit" and df.get(prop):
			if not saashq.db.get_value(
				"DocField", {"parent": self.doc_type, "fieldname": df.fieldname}, "allow_on_submit"
			):
				saashq.msgprint(
					_("Row {0}: Not allowed to enable Allow on Submit for standard fields").format(df.idx)
				)
				return False

		elif prop == "reqd" and (
			(
				saashq.db.get_value("DocField", {"parent": self.doc_type, "fieldname": df.fieldname}, "reqd")
				== 1
			)
			and (df.get(prop) == 0)
		):
			saashq.msgprint(_("Row {0}: Not allowed to disable Mandatory for standard fields").format(df.idx))
			return False

		elif (
			prop == "in_list_view"
			and df.get(prop)
			and df.fieldtype != "Attach Image"
			and df.fieldtype in no_value_fields
		):
			saashq.msgprint(
				_("'In List View' not allowed for type {0} in row {1}").format(df.fieldtype, df.idx)
			)
			return False

		elif (
			prop == "precision"
			and cint(df.get("precision")) > 6
			and cint(df.get("precision")) > cint(meta_df[0].get("precision"))
		):
			self.flags.update_db = True

		elif prop == "unique":
			self.flags.update_db = True

		elif (
			prop == "read_only"
			and cint(df.get("read_only")) == 0
			and saashq.db.get_value(
				"DocField", {"parent": self.doc_type, "fieldname": df.fieldname}, "read_only"
			)
			== 1
		):
			# if docfield has read_only checked and user is trying to make it editable, don't allow it
			saashq.msgprint(_("You cannot unset 'Read Only' for field {0}").format(df.label))
			return False

		elif prop == "options" and df.get("fieldtype") not in ALLOWED_OPTIONS_CHANGE:
			saashq.msgprint(_("You can't set 'Options' for field {0}").format(df.label))
			return False

		elif prop == "translatable" and not supports_translation(df.get("fieldtype")):
			saashq.msgprint(_("You can't set 'Translatable' for field {0}").format(df.label))
			return False

		elif prop == "in_global_search" and df.in_global_search != meta_df[0].get("in_global_search"):
			self.flags.rebuild_doctype_for_global_search = True

		return True

	def set_property_setters_for_actions_and_links(self, meta):
		"""
		Apply property setters or create custom records for DocType Action and DocType Link
		"""
		for doctype, fieldname, field_map in (
			("DocType Link", "links", doctype_link_properties),
			("DocType Action", "actions", doctype_action_properties),
			("DocType State", "states", doctype_state_properties),
		):
			has_custom = False
			items = []
			for i, d in enumerate(self.get(fieldname) or []):
				d.idx = i
				if saashq.db.exists(doctype, d.name) and not d.custom:
					# check property and apply property setter
					original = saashq.get_doc(doctype, d.name)
					for prop, prop_type in field_map.items():
						if d.get(prop) != original.get(prop):
							self.make_property_setter(
								prop, d.get(prop), prop_type, apply_on=doctype, row_name=d.name
							)
					items.append(d.name)
				else:
					# custom - just insert/update
					d.parent = self.doc_type
					d.custom = 1
					d.save(ignore_permissions=True)
					has_custom = True
					items.append(d.name)

			self.update_order_property_setter(has_custom, fieldname)
			self.clear_removed_items(doctype, items)

	def update_order_property_setter(self, has_custom, fieldname):
		"""
		We need to maintain the order of the link/actions if the user has shuffled them.
		So we create a new property (ex `links_order`) to keep a list of items.
		"""
		property_name = f"{fieldname}_order"
		if has_custom:
			# save the order of the actions and links
			self.make_property_setter(
				property_name, json.dumps([d.name for d in self.get(fieldname)]), "Small Text"
			)
		else:
			delete_property_setter(self.doc_type, property=property_name)

	def clear_removed_items(self, doctype, items):
		"""
		Clear rows that do not appear in `items`. These have been removed by the user.
		"""
		if items:
			saashq.db.delete(doctype, dict(parent=self.doc_type, custom=1, name=("not in", items)))
		else:
			saashq.db.delete(doctype, dict(parent=self.doc_type, custom=1))

	def update_custom_fields(self):
		for i, df in enumerate(self.get("fields")):
			if is_standard_or_system_generated_field(df):
				continue

			if not saashq.db.exists("Custom Field", {"dt": self.doc_type, "fieldname": df.fieldname}):
				self.add_custom_field(df, i)
				self.flags.update_db = True
			else:
				self.update_in_custom_field(df, i)

		self.delete_custom_fields()

	def add_custom_field(self, df, i):
		d = saashq.new_doc("Custom Field")

		d.dt = self.doc_type

		for prop in docfield_properties:
			d.set(prop, df.get(prop))

		if i != 0:
			d.insert_after = self.fields[i - 1].fieldname
		d.idx = i

		d.insert()
		df.fieldname = d.fieldname

		if df.get("in_global_search"):
			self.flags.rebuild_doctype_for_global_search = True

	def update_in_custom_field(self, df, i):
		meta = saashq.get_meta(self.doc_type)
		meta_df = meta.get("fields", {"fieldname": df.fieldname})
		if not meta_df or is_standard_or_system_generated_field(meta_df[0]):
			# not a custom field
			return

		custom_field = saashq.get_doc("Custom Field", meta_df[0].name)
		changed = False
		for prop in docfield_properties:
			if df.get(prop) != custom_field.get(prop):
				if prop == "fieldtype":
					self.validate_fieldtype_change(df, meta_df[0].get(prop), df.get(prop))
				if prop == "in_global_search":
					self.flags.rebuild_doctype_for_global_search = True

				custom_field.set(prop, df.get(prop))
				changed = True

		# check and update `insert_after` property
		if i != 0:
			insert_after = self.fields[i - 1].fieldname
			if custom_field.insert_after != insert_after:
				custom_field.insert_after = insert_after
				custom_field.idx = i
				changed = True

		if changed:
			custom_field.db_update()
			self.flags.update_db = True
			# custom_field.save()

	def delete_custom_fields(self):
		meta = saashq.get_meta(self.doc_type)
		fields_to_remove = {df.fieldname for df in meta.get("fields")} - {
			df.fieldname for df in self.get("fields")
		}
		for fieldname in fields_to_remove:
			df = meta.get("fields", {"fieldname": fieldname})[0]
			if not is_standard_or_system_generated_field(df):
				saashq.delete_doc("Custom Field", df.name)

	def make_property_setter(self, prop, value, property_type, fieldname=None, apply_on=None, row_name=None):
		delete_property_setter(self.doc_type, prop, fieldname, row_name)

		property_value = self.get_existing_property_value(prop, fieldname)

		if property_value == value:
			return

		if not apply_on:
			apply_on = "DocField" if fieldname else "DocType"

		# create a new property setter
		saashq.make_property_setter(
			{
				"doctype": self.doc_type,
				"doctype_or_field": apply_on,
				"fieldname": fieldname,
				"row_name": row_name,
				"property": prop,
				"value": value,
				"property_type": property_type,
			},
			is_system_generated=False,
		)

	def get_existing_property_value(self, property_name, fieldname=None):
		# check if there is any need to make property setter!
		if fieldname:
			property_value = saashq.db.get_value(
				"DocField", {"parent": self.doc_type, "fieldname": fieldname}, property_name
			)
		else:
			if saashq.db.has_column("DocType", property_name):
				property_value = saashq.db.get_value("DocType", self.doc_type, property_name)
			else:
				property_value = None

		return property_value

	def validate_fieldtype_change(self, df, old_value, new_value):
		if df.is_virtual:
			return

		allowed = self.allow_fieldtype_change(old_value, new_value)
		if allowed:
			old_value_length = cint(saashq.db.type_map.get(old_value)[1])
			new_value_length = cint(saashq.db.type_map.get(new_value)[1])

			# Ignore fieldtype check validation if new field type has unspecified maxlength
			# Changes like DATA to TEXT, where new_value_lenth equals 0 will not be validated
			if new_value_length and (old_value_length > new_value_length):
				self.check_length_for_fieldtypes.append({"df": df, "old_value": old_value})
				self.validate_fieldtype_length()
			else:
				self.flags.update_db = True

		else:
			saashq.throw(
				_("Fieldtype cannot be changed from {0} to {1} in row {2}").format(
					old_value, new_value, df.idx
				)
			)

	def validate_fieldtype_length(self):
		for field in self.check_length_for_fieldtypes:
			df = field.get("df")
			max_length = cint(saashq.db.type_map.get(df.fieldtype)[1])
			fieldname = df.fieldname
			docs = saashq.db.sql(
				f"""
				SELECT name, {fieldname}, LENGTH({fieldname}) AS len
				FROM `tab{self.doc_type}`
				WHERE LENGTH({fieldname}) > {max_length}
			""",
				as_dict=True,
			)
			label = df.label
			links_str = ", ".join(saashq.utils.get_link_to_form(self.doc_type, doc.name) for doc in docs)

			if docs:
				saashq.throw(
					_(
						"Value for field {0} is too long in {1}. Length should be lesser than {2} characters"
					).format(saashq.bold(label), links_str, saashq.bold(max_length)),
					title=_("Data Too Long"),
					is_minimizable=len(docs) > 1,
				)

		self.flags.update_db = True

	@saashq.whitelist()
	def reset_to_defaults(self):
		if not self.doc_type:
			return

		reset_customization(self.doc_type)
		self.fetch_to_customize()

	@saashq.whitelist()
	def reset_layout(self):
		if not self.doc_type:
			return

		property_setters = saashq.get_all(
			"Property Setter",
			filters={"doc_type": self.doc_type, "property": ("in", ("field_order", "insert_after"))},
			pluck="name",
		)

		if not property_setters:
			return

		saashq.db.delete("Property Setter", {"name": ("in", property_setters)})
		saashq.clear_cache(doctype=self.doc_type)
		self.fetch_to_customize()

	@saashq.whitelist()
	def trim_table(self):
		"""Removes database fields that don't exist in the doctype.

		This may be needed as maintenance since removing a field in a DocType
		doesn't automatically delete the db field.
		"""
		if not self.doc_type:
			return

		trim_table(self.doc_type, dry_run=False)
		self.fetch_to_customize()

	@classmethod
	def allow_fieldtype_change(self, old_type: str, new_type: str) -> bool:
		"""allow type change, if both old_type and new_type are in same field group.
		field groups are defined in ALLOWED_FIELDTYPE_CHANGE variables.
		"""

		def in_field_group(group):
			return (old_type in group) and (new_type in group)

		return any(map(in_field_group, ALLOWED_FIELDTYPE_CHANGE))


@saashq.whitelist()
def get_orphaned_columns(doctype: str):
	saashq.only_for("System Manager")
	saashq.db.begin(read_only=True)  # Avoid any potential bug from writing to db
	return trim_table(doctype, dry_run=True)


def reset_customization(doctype):
	setters = saashq.get_all(
		"Property Setter",
		filters={
			"doc_type": doctype,
			"field_name": ["!=", "naming_series"],
			"property": ["!=", "options"],
			"is_system_generated": False,
		},
		pluck="name",
	)

	for setter in setters:
		saashq.delete_doc("Property Setter", setter)

	custom_fields = saashq.get_all(
		"Custom Field", filters={"dt": doctype, "is_system_generated": False}, pluck="name"
	)

	for field in custom_fields:
		saashq.delete_doc("Custom Field", field)

	saashq.clear_cache(doctype=doctype)


def is_standard_or_system_generated_field(df):
	return not df.get("is_custom_field") or df.get("is_system_generated")


@saashq.whitelist()
def get_link_filters_from_doc_without_customisations(doctype, fieldname):
	"""Get the filters of a link field from a doc without customisations
	In backend the customisations are not applied.
	Customisations are applied in the client side.
	"""
	doc = saashq.get_doc("DocType", doctype)
	field = list(filter(lambda x: x.fieldname == fieldname, doc.fields))
	return field[0].link_filters


doctype_properties = {
	"search_fields": "Data",
	"title_field": "Data",
	"image_field": "Data",
	"sort_field": "Data",
	"sort_order": "Data",
	"default_print_format": "Data",
	"allow_copy": "Check",
	"istable": "Check",
	"quick_entry": "Check",
	"queue_in_background": "Check",
	"editable_grid": "Check",
	"max_attachments": "Int",
	"make_attachments_public": "Check",
	"track_changes": "Check",
	"track_views": "Check",
	"allow_auto_repeat": "Check",
	"allow_import": "Check",
	"show_preview_popup": "Check",
	"default_email_template": "Data",
	"email_append_to": "Check",
	"subject_field": "Data",
	"sender_field": "Data",
	"naming_rule": "Data",
	"autoname": "Data",
	"show_title_field_in_link": "Check",
	"is_calendar_and_gantt": "Check",
	"default_view": "Select",
	"force_re_route_to_default_view": "Check",
	"translated_doctype": "Check",
}

docfield_properties = {
	"idx": "Int",
	"label": "Data",
	"fieldtype": "Select",
	"options": "Text",
	"sort_options": "Check",
	"fetch_from": "Small Text",
	"fetch_if_empty": "Check",
	"show_dashboard": "Check",
	"permlevel": "Int",
	"width": "Data",
	"print_width": "Data",
	"non_negative": "Check",
	"reqd": "Check",
	"unique": "Check",
	"ignore_user_permissions": "Check",
	"in_list_view": "Check",
	"in_standard_filter": "Check",
	"in_global_search": "Check",
	"in_preview": "Check",
	"bold": "Check",
	"no_copy": "Check",
	"ignore_xss_filter": "Check",
	"hidden": "Check",
	"collapsible": "Check",
	"collapsible_depends_on": "Data",
	"print_hide": "Check",
	"print_hide_if_no_value": "Check",
	"report_hide": "Check",
	"allow_on_submit": "Check",
	"translatable": "Check",
	"mandatory_depends_on": "Data",
	"read_only_depends_on": "Data",
	"depends_on": "Data",
	"description": "Text",
	"default": "Text",
	"precision": "Select",
	"read_only": "Check",
	"length": "Int",
	"columns": "Int",
	"remember_last_selected_value": "Check",
	"allow_bulk_edit": "Check",
	"auto_repeat": "Link",
	"allow_in_quick_entry": "Check",
	"hide_border": "Check",
	"hide_days": "Check",
	"hide_seconds": "Check",
	"is_virtual": "Check",
	"link_filters": "JSON",
	"placeholder": "Data",
}

doctype_link_properties = {
	"link_doctype": "Link",
	"link_fieldname": "Data",
	"group": "Data",
	"hidden": "Check",
}

doctype_action_properties = {
	"label": "Link",
	"action_type": "Select",
	"action": "Small Text",
	"group": "Data",
	"hidden": "Check",
}

doctype_state_properties = {"title": "Data", "color": "Select"}


ALLOWED_FIELDTYPE_CHANGE = (
	("Currency", "Float", "Percent"),
	("Small Text", "Data"),
	("Text", "Data"),
	("Text", "Text Editor", "Code", "Signature", "HTML Editor"),
	("Data", "Select"),
	("Text", "Small Text", "Long Text"),
	("Text", "Data", "Barcode"),
	("Code", "Geolocation"),
	("Table", "Table MultiSelect"),
)

ALLOWED_OPTIONS_CHANGE = ("Read Only", "HTML", "Data")
