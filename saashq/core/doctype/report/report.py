# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE
import datetime
import json

import saashq
import saashq.desk.query_report
from saashq import _, scrub
from saashq.core.doctype.custom_role.custom_role import get_custom_allowed_roles
from saashq.core.doctype.page.page import delete_custom_role
from saashq.desk.reportview import append_totals_row
from saashq.model.document import Document
from saashq.modules import make_boilerplate
from saashq.modules.export_file import export_to_files
from saashq.utils import cint, cstr
from saashq.utils.safe_exec import check_safe_sql_query, safe_exec


class Report(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.core.doctype.has_role.has_role import HasRole
		from saashq.core.doctype.report_column.report_column import ReportColumn
		from saashq.core.doctype.report_filter.report_filter import ReportFilter
		from saashq.types import DF

		add_total_row: DF.Check
		columns: DF.Table[ReportColumn]
		disabled: DF.Check
		filters: DF.Table[ReportFilter]
		is_standard: DF.Literal["No", "Yes"]
		javascript: DF.Code | None
		json: DF.Code | None
		letter_head: DF.Link | None
		module: DF.Link | None
		prepared_report: DF.Check
		query: DF.Code | None
		ref_doctype: DF.Link
		reference_report: DF.Data | None
		report_name: DF.Data
		report_script: DF.Code | None
		report_type: DF.Literal["Report Builder", "Query Report", "Script Report", "Custom Report"]
		roles: DF.Table[HasRole]
		timeout: DF.Int
	# end: auto-generated types

	def validate(self):
		"""only administrator can save standard report"""
		if not self.module:
			self.module = saashq.db.get_value("DocType", self.ref_doctype, "module")

		if not self.is_standard:
			self.is_standard = "No"
			if (
				saashq.session.user == "Administrator"
				and getattr(saashq.local.conf, "developer_mode", 0) == 1
			):
				self.is_standard = "Yes"

		if self.is_standard == "No":
			# allow only script manager to edit scripts
			if self.report_type != "Report Builder":
				saashq.only_for("Script Manager", True)

			if saashq.db.get_value("Report", self.name, "is_standard") == "Yes":
				saashq.throw(_("Cannot edit a standard report. Please duplicate and create a new report"))

		if self.is_standard == "Yes" and saashq.session.user != "Administrator":
			saashq.throw(_("Only Administrator can save a standard report. Please rename and save."))

		if self.report_type == "Report Builder":
			self.update_report_json()

	def before_insert(self):
		self.set_doctype_roles()

	def on_update(self):
		self.export_doc()

	def before_export(self, doc):
		doc.letterhead = None
		doc.prepared_report = 0

	def on_trash(self):
		if (
			self.is_standard == "Yes"
			and not cint(getattr(saashq.local.conf, "developer_mode", 0))
			and not saashq.flags.in_migrate
			and not saashq.flags.in_patch
		):
			saashq.throw(_("You are not allowed to delete Standard Report"))
		delete_custom_role("report", self.name)

	def get_permission_log_options(self, event=None):
		return {"fields": ["roles"]}

	def get_columns(self):
		return [d.as_dict(no_default_fields=True, no_child_table_fields=True) for d in self.columns]

	@saashq.whitelist()
	def set_doctype_roles(self):
		if not self.get("roles") and self.is_standard == "No":
			meta = saashq.get_meta(self.ref_doctype)
			if not meta.istable:
				roles = [{"role": d.role} for d in meta.permissions if d.permlevel == 0]
				self.set("roles", roles)

	def is_permitted(self):
		"""Return True if `Has Role` is not set or the user is allowed."""
		from saashq.utils import has_common

		allowed = [d.role for d in saashq.get_all("Has Role", fields=["role"], filters={"parent": self.name})]

		custom_roles = get_custom_allowed_roles("report", self.name)

		if custom_roles:
			allowed = custom_roles

		if not allowed:
			return True

		if has_common(saashq.get_roles(), allowed):
			return True

	def update_report_json(self):
		if not self.json:
			self.json = "{}"

	def export_doc(self):
		if saashq.flags.in_import:
			return

		if self.is_standard == "Yes" and saashq.conf.developer_mode:
			export_to_files(record_list=[["Report", self.name]], record_module=self.module, create_init=True)

			self.create_report_py()

	def create_report_py(self):
		if self.report_type == "Script Report":
			make_boilerplate("controller.py", self, {"name": self.name})
			make_boilerplate("controller.js", self, {"name": self.name})

	def execute_query_report(self, filters):
		if not self.query:
			saashq.throw(_("Must specify a Query to run"), title=_("Report Document Error"))

		check_safe_sql_query(self.query)

		result = [list(t) for t in saashq.db.sql(self.query, filters)]
		columns = self.get_columns() or [cstr(c[0]) for c in saashq.db.get_description()]

		return [columns, result]

	def execute_script_report(self, filters):
		# save the timestamp to automatically set to prepared
		threshold = 15

		start_time = datetime.datetime.now()

		# The JOB
		if self.is_standard == "Yes":
			res = self.execute_module(filters)
		else:
			res = self.execute_script(filters)

		# automatically set as prepared
		execution_time = (datetime.datetime.now() - start_time).total_seconds()
		if execution_time > threshold and not self.prepared_report and not saashq.conf.developer_mode:
			saashq.enqueue(enable_prepared_report, report=self.name)

		saashq.cache.hset("report_execution_time", self.name, execution_time)

		return res

	def execute_module(self, filters):
		# report in python module
		module = self.module or saashq.db.get_value("DocType", self.ref_doctype, "module")
		method_name = get_report_module_dotted_path(module, self.name) + ".execute"
		return saashq.get_attr(method_name)(saashq._dict(filters))

	def execute_script(self, filters):
		# server script
		loc = {"filters": saashq._dict(filters), "data": None, "result": None}
		safe_exec(self.report_script, None, loc, script_filename=f"Report {self.name}")
		if loc["data"]:
			return loc["data"]
		else:
			return self.get_columns(), loc["result"]

	def get_data(
		self,
		filters=None,
		limit=None,
		user=None,
		as_dict=False,
		ignore_prepared_report=False,
		are_default_filters=True,
	):
		if self.report_type in ("Query Report", "Script Report", "Custom Report"):
			columns, result = self.run_query_report(
				filters, user, ignore_prepared_report, are_default_filters
			)
		else:
			columns, result = self.run_standard_report(filters, limit, user)

		if as_dict:
			result = self.build_data_dict(result, columns)

		return columns, result

	def run_query_report(
		self, filters=None, user=None, ignore_prepared_report=False, are_default_filters=True
	):
		columns, result = [], []
		data = saashq.desk.query_report.run(
			self.name,
			filters=filters,
			user=user,
			ignore_prepared_report=ignore_prepared_report,
			are_default_filters=are_default_filters,
		)

		for d in data.get("columns"):
			if isinstance(d, dict):
				col = saashq._dict(d)
				if not col.fieldname:
					col.fieldname = col.label
				columns.append(col)
			else:
				fieldtype, options = "Data", None
				parts = d.split(":")
				if len(parts) > 1:
					if parts[1]:
						fieldtype, options = parts[1], None
						if fieldtype and "/" in fieldtype:
							fieldtype, options = fieldtype.split("/")

				columns.append(
					saashq._dict(label=parts[0], fieldtype=fieldtype, fieldname=parts[0], options=options)
				)

		result += data.get("result")

		return columns, result

	def run_standard_report(self, filters, limit, user):
		params = json.loads(self.json)
		columns = self.get_standard_report_columns(params)
		result = []
		order_by, group_by, group_by_args = self.get_standard_report_order_by(params)

		_result = saashq.get_list(
			self.ref_doctype,
			fields=[
				get_group_by_field(group_by_args, c[1])
				if c[0] == "_aggregate_column" and group_by_args
				else Report._format([c[1], c[0]])
				for c in columns
			],
			filters=self.get_standard_report_filters(params, filters),
			order_by=order_by,
			group_by=group_by,
			as_list=True,
			limit=limit,
			user=user,
		)

		columns = self.build_standard_report_columns(columns, group_by_args)

		result = result + [list(d) for d in _result]

		if params.get("add_totals_row"):
			result = append_totals_row(result)

		return columns, result

	@staticmethod
	def _format(parts):
		# sort by is saved as DocType.fieldname, covert it to sql
		return "`tab{}`.`{}`".format(*parts)

	def get_standard_report_columns(self, params):
		if params.get("fields"):
			columns = params.get("fields")
		elif params.get("columns"):
			columns = params.get("columns")
		elif params.get("fields"):
			columns = params.get("fields")
		else:
			columns = [["name", self.ref_doctype]]
			columns.extend(
				[df.fieldname, self.ref_doctype]
				for df in saashq.get_meta(self.ref_doctype).fields
				if df.in_list_view
			)
		return columns

	def get_standard_report_filters(self, params, filters):
		_filters = params.get("filters") or []

		if filters:
			for key, value in filters.items():
				condition, _value = "=", value
				if isinstance(value, list | tuple):
					condition, _value = value
				_filters.append([key, condition, _value])

		return _filters

	def get_standard_report_order_by(self, params):
		group_by_args = None
		if params.get("sort_by"):
			order_by = Report._format(params.get("sort_by").split(".")) + " " + params.get("sort_order")

		elif params.get("order_by"):
			order_by = params.get("order_by")
		else:
			order_by = Report._format([self.ref_doctype, "creation"]) + " desc"

		if params.get("sort_by_next"):
			order_by += (
				", "
				+ Report._format(params.get("sort_by_next").split("."))
				+ " "
				+ params.get("sort_order_next")
			)

		group_by = None
		if params.get("group_by"):
			group_by_args = saashq._dict(params["group_by"])
			group_by = group_by_args["group_by"]
			order_by = "_aggregate_column desc"

		return order_by, group_by, group_by_args

	def build_standard_report_columns(self, columns, group_by_args):
		_columns = []

		for fieldname, doctype in columns:
			meta = saashq.get_meta(doctype)

			if meta.get_field(fieldname):
				field = meta.get_field(fieldname)
			else:
				if fieldname == "_aggregate_column":
					label = get_group_by_column_label(group_by_args, meta)
				else:
					label = meta.get_label(fieldname)

				field = saashq._dict(fieldname=fieldname, label=label)

				# since name is the primary key for a document, it will always be a Link datatype
				if fieldname == "name":
					field.fieldtype = "Link"
					field.options = doctype

			_columns.append(field)
		return _columns

	def build_data_dict(self, result, columns):
		data = []
		for row in result:
			if isinstance(row, list | tuple):
				_row = saashq._dict()
				for i, val in enumerate(row):
					_row[columns[i].get("fieldname")] = val
			elif isinstance(row, dict):
				# no need to convert from dict to dict
				_row = saashq._dict(row)
			data.append(_row)

		return data

	@saashq.whitelist()
	def toggle_disable(self, disable: bool):
		if not self.has_permission("write"):
			saashq.throw(_("You are not allowed to edit the report."))

		self.db_set("disabled", cint(disable))


def is_prepared_report_enabled(report):
	return cint(saashq.db.get_value("Report", report, "prepared_report"))


def get_report_module_dotted_path(module, report_name):
	return (
		saashq.local.module_app[scrub(module)]
		+ "."
		+ scrub(module)
		+ ".report."
		+ scrub(report_name)
		+ "."
		+ scrub(report_name)
	)


def get_group_by_field(args, doctype):
	if args["aggregate_function"] == "count":
		group_by_field = "count(*) as _aggregate_column"
	else:
		group_by_field = f"{args.aggregate_function}({args.aggregate_on}) as _aggregate_column"

	return group_by_field


def get_group_by_column_label(args, meta):
	if args["aggregate_function"] == "count":
		label = "Count"
	else:
		sql_fn_map = {"avg": "Average", "sum": "Sum"}
		aggregate_on_label = meta.get_label(args.aggregate_on)
		label = _("{0} of {1}").format(_(sql_fn_map[args.aggregate_function]), _(aggregate_on_label))
	return label


def enable_prepared_report(report: str):
	saashq.db.set_value("Report", report, "prepared_report", 1)
