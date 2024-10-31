# Copyleft (l) 2023-Present, Saashq Technologies and contributors
# License: MIT. See LICENSE

from typing import Protocol, runtime_checkable

import saashq
from saashq import _
from saashq.model.base_document import get_controller
from saashq.model.document import Document
from saashq.utils import cint
from saashq.utils.caching import site_cache


@runtime_checkable
class LogType(Protocol):
	"""Interface requirement for doctypes that can be cleared using log settings."""

	@staticmethod
	def clear_old_logs(days: int) -> None:
		...


@site_cache
def _supports_log_clearing(doctype: str) -> bool:
	try:
		controller = get_controller(doctype)
		return issubclass(controller, LogType)
	except Exception:
		return False


class LogSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.core.doctype.logs_to_clear.logs_to_clear import LogsToClear
		from saashq.types import DF

		logs_to_clear: DF.Table[LogsToClear]
	# end: auto-generated types

	def validate(self):
		self.remove_unsupported_doctypes()
		self._deduplicate_entries()
		self.add_default_logtypes()

	def remove_unsupported_doctypes(self):
		for entry in list(self.logs_to_clear):
			if _supports_log_clearing(entry.ref_doctype):
				continue

			msg = _("{} does not support automated log clearing.").format(saashq.bold(entry.ref_doctype))
			if saashq.conf.developer_mode:
				msg += "<br>" + _("Implement `clear_old_logs` method to enable auto error clearing.")
			saashq.msgprint(msg, title=_("DocType not supported by Log Settings."))
			self.remove(entry)

	def _deduplicate_entries(self):
		seen = set()
		for entry in list(self.logs_to_clear):
			if entry.ref_doctype in seen:
				self.remove(entry)
			seen.add(entry.ref_doctype)

	def add_default_logtypes(self):
		existing_logtypes = {d.ref_doctype for d in self.logs_to_clear}
		added_logtypes = set()
		default_logtypes_retention = saashq.get_hooks("default_log_clearing_doctypes", {})

		for logtype, retentions in default_logtypes_retention.items():
			if logtype not in existing_logtypes and _supports_log_clearing(logtype):
				if not saashq.db.exists("DocType", logtype):
					continue

				self.append("logs_to_clear", {"ref_doctype": logtype, "days": cint(retentions[-1])})
				added_logtypes.add(logtype)

		if added_logtypes:
			saashq.msgprint(_("Added default log doctypes: {}").format(",".join(added_logtypes)), alert=True)

	def clear_logs(self):
		"""
		Log settings can clear any log type that's registered to it and provides a method to delete old logs.

		Check `LogDoctype` above for interface that doctypes need to implement.
		"""

		for entry in self.logs_to_clear:
			controller: LogType = get_controller(entry.ref_doctype)
			func = controller.clear_old_logs

			# Only pass what the method can handle, this is considering any
			# future addition that might happen to the required interface.
			kwargs = saashq.get_newargs(func, {"days": entry.days})
			func(**kwargs)
			saashq.db.commit()

	def register_doctype(self, doctype: str, days=30):
		existing_logtypes = {d.ref_doctype for d in self.logs_to_clear}

		if doctype not in existing_logtypes and _supports_log_clearing(doctype):
			self.append("logs_to_clear", {"ref_doctype": doctype, "days": cint(days)})
		else:
			for entry in self.logs_to_clear:
				if entry.ref_doctype == doctype:
					entry.days = days
					break


def run_log_clean_up():
	doc = saashq.get_doc("Log Settings")
	doc.remove_unsupported_doctypes()
	doc.add_default_logtypes()
	doc.save()
	doc.clear_logs()


@saashq.whitelist()
def has_unseen_error_log():
	if saashq.get_all("Error Log", filters={"seen": 0}, limit=1):
		return {
			"show_alert": True,
			"message": _("You have unseen {0}").format(
				'<a href="/app/List/Error%20Log/List"> Error Logs </a>'
			),
		}


@saashq.whitelist()
@saashq.validate_and_sanitize_search_inputs
def get_log_doctypes(doctype, txt, searchfield, start, page_len, filters):
	filters = filters or {}

	filters.extend(
		[
			["istable", "=", 0],
			["issingle", "=", 0],
			["name", "like", f"%%{txt}%%"],
		]
	)
	doctypes = saashq.get_list("DocType", filters=filters, pluck="name")

	supported_doctypes = [(d,) for d in doctypes if _supports_log_clearing(d)]

	return supported_doctypes[start:page_len]


LOG_DOCTYPES = [
	"Scheduled Job Log",
	"Activity Log",
	"Route History",
	"Email Queue",
	"Email Queue Recipient",
	"Error Log",
]


def clear_log_table(doctype, days=90):
	"""If any logtype table grows too large then clearing it with DELETE query
	is not feasible in reasonable time. This command copies recent data to new
	table and replaces current table with new smaller table.

	ref: https://mariadb.com/kb/en/big-deletes/#deleting-more-than-half-a-table
	"""
	from saashq.utils import get_table_name

	if doctype not in LOG_DOCTYPES:
		raise saashq.ValidationError(f"Unsupported logging DocType: {doctype}")

	original = get_table_name(doctype)
	temporary = f"{original} temp_table"
	backup = f"{original} backup_table"

	try:
		saashq.db.sql_ddl(f"CREATE TABLE `{temporary}` LIKE `{original}`")

		# Copy all recent data to new table
		saashq.db.sql(
			f"""INSERT INTO `{temporary}`
				SELECT * FROM `{original}`
				WHERE `{original}`.`creation` > NOW() - INTERVAL '{days}' DAY"""
		)
		saashq.db.sql_ddl(f"RENAME TABLE `{original}` TO `{backup}`, `{temporary}` TO `{original}`")
	except Exception:
		saashq.db.rollback()
		saashq.db.sql_ddl(f"DROP TABLE IF EXISTS `{temporary}`")
		raise
	else:
		saashq.db.sql_ddl(f"DROP TABLE `{backup}`")
