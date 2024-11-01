# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import calendar
import datetime
from datetime import timedelta
from email.utils import formataddr

import saashq
from saashq import _
from saashq.desk.query_report import build_xlsx_data
from saashq.model.document import Document
from saashq.model.naming import append_number_if_name_exists
from saashq.utils import (
	add_to_date,
	cint,
	format_time,
	get_first_day,
	get_first_day_of_week,
	get_link_to_form,
	get_quarter_start,
	get_url_to_report,
	get_year_start,
	getdate,
	global_date_format,
	now,
	now_datetime,
	today,
	validate_email_address,
)
from saashq.utils.csvutils import to_csv
from saashq.utils.xlsxutils import make_xlsx


class AutoEmailReport(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		data_modified_till: DF.Int
		day_of_week: DF.Literal["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
		description: DF.TextEditor | None
		dynamic_date_period: DF.Literal[
			"", "Daily", "Weekly", "Monthly", "Quarterly", "Half Yearly", "Yearly"
		]
		email_to: DF.SmallText
		enabled: DF.Check
		filter_meta: DF.Text | None
		filters: DF.Text | None
		format: DF.Literal["HTML", "XLSX", "CSV"]
		frequency: DF.Literal["Daily", "Weekdays", "Weekly", "Monthly"]
		from_date_field: DF.Literal[None]
		no_of_rows: DF.Int
		reference_report: DF.Data | None
		report: DF.Link
		report_type: DF.ReadOnly | None
		send_if_data: DF.Check
		sender: DF.Link | None
		to_date_field: DF.Literal[None]
		use_first_day_of_period: DF.Check
		user: DF.Link
	# end: auto-generated types

	def autoname(self):
		self.name = _(self.report)
		if saashq.db.exists("Auto Email Report", self.name):
			self.name = append_number_if_name_exists("Auto Email Report", self.name)

	def validate(self):
		self.validate_report_count()
		self.validate_emails()
		self.validate_report_format()
		self.validate_mandatory_fields()

	@property
	def sender_email(self):
		return saashq.db.get_value("Email Account", self.sender, "email_id")

	def validate_emails(self):
		"""Cleanup list of emails"""
		if "," in self.email_to:
			self.email_to.replace(",", "\n")

		valid = []
		for email in self.email_to.split():
			if email:
				validate_email_address(email, True)
				valid.append(email)

		self.email_to = "\n".join(valid)

	def validate_report_count(self):
		count = saashq.db.count("Auto Email Report", {"user": self.user, "enabled": 1})

		max_reports_per_user = (
			cint(saashq.local.conf.max_reports_per_user)  # kept for backward compatibilty
			or cint(saashq.get_system_settings("max_auto_email_report_per_user"))
			or 20
		)

		if count > max_reports_per_user + (-1 if self.flags.in_insert else 0):
			msg = _("Only {0} emailed reports are allowed per user.").format(max_reports_per_user)
			msg += " " + _("To allow more reports update limit in System Settings.")
			saashq.throw(msg, title=_("Report limit reached"))

	def validate_report_format(self):
		"""check if user has select correct report format"""
		valid_report_formats = ["HTML", "XLSX", "CSV"]
		if self.format not in valid_report_formats:
			saashq.throw(
				_("{0} is not a valid report format. Report format should one of the following {1}").format(
					saashq.bold(self.format), saashq.bold(", ".join(valid_report_formats))
				)
			)

	def validate_mandatory_fields(self):
		# Check if all Mandatory Report Filters are filled by the User
		filters = saashq.parse_json(self.filters) if self.filters else {}
		filter_meta = saashq.parse_json(self.filter_meta) if self.filter_meta else {}
		throw_list = [
			meta["label"] for meta in filter_meta if meta.get("reqd") and not filters.get(meta["fieldname"])
		]
		if throw_list:
			saashq.throw(
				title=_("Missing Filters Required"),
				msg=_("Following Report Filters have missing values:")
				+ "<br><br><ul><li>"
				+ " <li>".join(throw_list)
				+ "</ul>",
			)

	def get_report_content(self):
		"""Return file for the report in given format."""
		report = saashq.get_doc("Report", self.report)

		self.filters = saashq.parse_json(self.filters) if self.filters else {}

		if self.report_type == "Report Builder" and self.data_modified_till:
			self.filters["modified"] = (">", now_datetime() - timedelta(hours=self.data_modified_till))

		if self.report_type != "Report Builder" and self.dynamic_date_filters_set():
			self.prepare_dynamic_filters()

		columns, data = report.get_data(
			limit=self.no_of_rows or 100,
			user=self.user,
			filters=self.filters,
			as_dict=True,
			ignore_prepared_report=True,
			are_default_filters=False,
		)

		# add serial numbers
		columns.insert(0, saashq._dict(fieldname="idx", label="", width="30px"))
		for i in range(len(data)):
			data[i]["idx"] = i + 1

		if len(data) == 0 and self.send_if_data:
			return None

		if self.format == "HTML":
			columns, data = make_links(columns, data)
			columns = update_field_types(columns)
			return self.get_html_table(columns, data)

		elif self.format == "XLSX":
			report_data = saashq._dict()
			report_data["columns"] = columns
			report_data["result"] = data

			xlsx_data, column_widths = build_xlsx_data(report_data, [], 1, ignore_visible_idx=True)
			xlsx_file = make_xlsx(xlsx_data, "Auto Email Report", column_widths=column_widths)
			return xlsx_file.getvalue()

		elif self.format == "CSV":
			report_data = saashq._dict()
			report_data["columns"] = columns
			report_data["result"] = data

			xlsx_data, column_widths = build_xlsx_data(report_data, [], 1, ignore_visible_idx=True)
			return to_csv(xlsx_data)

		else:
			saashq.throw(_("Invalid Output Format"))

	def get_html_table(self, columns=None, data=None):
		date_time = global_date_format(now()) + " " + format_time(now())
		report_doctype = saashq.db.get_value("Report", self.report, "ref_doctype")

		return saashq.render_template(
			"saashq/templates/emails/auto_email_report.html",
			{
				"title": self.name,
				"description": self.description,
				"date_time": date_time,
				"columns": columns,
				"data": data,
				"report_url": get_url_to_report(self.report, self.report_type, report_doctype),
				"report_name": self.report,
				"edit_report_settings": get_link_to_form("Auto Email Report", self.name),
			},
		)

	def get_file_name(self):
		return "{}.{}".format(self.report.replace(" ", "-").replace("/", "-"), self.format.lower())

	def prepare_dynamic_filters(self):
		self.filters = saashq.parse_json(self.filters)

		to_date = today()

		if self.use_first_day_of_period:
			from_date = to_date
			if self.dynamic_date_period == "Daily":
				from_date = add_to_date(to_date, days=-1)
			elif self.dynamic_date_period == "Weekly":
				from_date = get_first_day_of_week(from_date)
			elif self.dynamic_date_period == "Monthly":
				from_date = get_first_day(from_date)
			elif self.dynamic_date_period == "Quarterly":
				from_date = get_quarter_start(from_date)
			elif self.dynamic_date_period == "Half Yearly":
				from_date = get_half_year_start(from_date)
			elif self.dynamic_date_period == "Yearly":
				from_date = get_year_start(from_date)

			self.set_date_filters(from_date, to_date)
		else:
			from_date_value = {
				"Daily": ("days", -1),
				"Weekly": ("weeks", -1),
				"Monthly": ("months", -1),
				"Quarterly": ("months", -3),
				"Half Yearly": ("months", -6),
				"Yearly": ("years", -1),
			}[self.dynamic_date_period]

			from_date = add_to_date(to_date, **{from_date_value[0]: from_date_value[1]})
			self.set_date_filters(from_date, to_date)

	def set_date_filters(self, from_date, to_date):
		self.filters[self.from_date_field] = from_date
		self.filters[self.to_date_field] = to_date

	def send(self):
		if self.filter_meta and not self.filters:
			saashq.throw(_("Please set filters value in Report Filter table."))

		data = self.get_report_content()
		if not data:
			return

		attachments = None
		if self.format == "HTML":
			message = data
		else:
			message = self.get_html_table()

		if self.format != "HTML":
			attachments = [{"fname": self.get_file_name(), "fcontent": data}]

		saashq.sendmail(
			recipients=self.email_to.split(),
			sender=formataddr((self.sender, self.sender_email)) if self.sender else "",
			subject=self.name,
			message=message,
			attachments=attachments,
			reference_doctype=self.doctype,
			reference_name=self.name,
		)

	def dynamic_date_filters_set(self):
		return self.dynamic_date_period and self.from_date_field and self.to_date_field


@saashq.whitelist()
def download(name):
	"""Download report locally"""
	auto_email_report = saashq.get_doc("Auto Email Report", name)
	auto_email_report.check_permission()
	data = auto_email_report.get_report_content()

	if not data:
		saashq.msgprint(_("No Data"))
		return

	saashq.local.response.filecontent = data
	saashq.local.response.type = "download"
	saashq.local.response.filename = auto_email_report.get_file_name()


@saashq.whitelist()
def send_now(name):
	"""Send Auto Email report now"""
	auto_email_report = saashq.get_doc("Auto Email Report", name)
	auto_email_report.check_permission()
	auto_email_report.send()


def send_daily():
	"""Check reports to be sent daily"""

	current_day = calendar.day_name[now_datetime().weekday()]
	enabled_reports = saashq.get_all(
		"Auto Email Report", filters={"enabled": 1, "frequency": ("in", ("Daily", "Weekdays", "Weekly"))}
	)

	for report in enabled_reports:
		auto_email_report = saashq.get_doc("Auto Email Report", report.name)

		# if not correct weekday, skip
		if auto_email_report.frequency == "Weekdays":
			if current_day in ("Saturday", "Sunday"):
				continue
		elif auto_email_report.frequency == "Weekly":
			if auto_email_report.day_of_week != current_day:
				continue
		try:
			auto_email_report.send()
		except Exception:
			auto_email_report.log_error(f"Failed to send {auto_email_report.name} Auto Email Report")


def send_monthly():
	"""Check reports to be sent monthly"""
	for report in saashq.get_all("Auto Email Report", {"enabled": 1, "frequency": "Monthly"}):
		saashq.get_doc("Auto Email Report", report.name).send()


def make_links(columns, data):
	for row in data:
		doc_name = row.get("name")
		for col in columns:
			if not row.get(col.fieldname):
				continue

			if col.fieldtype == "Link":
				if col.options and col.options != "Currency":
					row[col.fieldname] = get_link_to_form(col.options, row[col.fieldname])
			elif col.fieldtype == "Dynamic Link":
				if col.options and row.get(col.options):
					row[col.fieldname] = get_link_to_form(row[col.options], row[col.fieldname])
			elif col.fieldtype == "Currency":
				doc = None
				if doc_name and col.get("parent") and not saashq.get_meta(col.parent).istable:
					if saashq.db.exists(col.parent, doc_name):
						doc = saashq.get_doc(col.parent, doc_name)

				# Pass the Document to get the currency based on docfield option
				row[col.fieldname] = saashq.format_value(row[col.fieldname], col, doc=doc)
	return columns, data


def update_field_types(columns):
	for col in columns:
		if col.fieldtype in ("Link", "Dynamic Link", "Currency") and col.options != "Currency":
			col.fieldtype = "Data"
			col.options = ""
	return columns


DATE_FORMAT = "%Y-%m-%d"


def get_half_year_start(as_str=False):
	"""
	Returns the first day of the current half-year based on the current date.
	"""
	today_date = getdate(today())

	half_year = 1 if today_date.month <= 6 else 2

	year = today_date.year if half_year == 1 else today_date.year + 1
	month = 1 if half_year == 1 else 7
	day = 1

	result_date = datetime.date(year, month, day)

	return result_date if not as_str else result_date.strftime(DATE_FORMAT)
