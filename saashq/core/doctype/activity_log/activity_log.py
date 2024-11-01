# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq
from saashq.core.utils import set_timeline_doc
from saashq.model.document import Document
from saashq.query_builder import DocType, Interval
from saashq.query_builder.functions import Now
from saashq.utils import get_fullname, now


class ActivityLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		communication_date: DF.Datetime | None
		content: DF.TextEditor | None
		full_name: DF.Data | None
		ip_address: DF.Data | None
		link_doctype: DF.Link | None
		link_name: DF.DynamicLink | None
		operation: DF.Literal["", "Login", "Logout", "Impersonate"]
		reference_doctype: DF.Link | None
		reference_name: DF.DynamicLink | None
		reference_owner: DF.ReadOnly | None
		status: DF.Literal["", "Success", "Failed", "Linked", "Closed"]
		subject: DF.SmallText
		timeline_doctype: DF.Link | None
		timeline_name: DF.DynamicLink | None
		user: DF.Link | None
	# end: auto-generated types

	def before_insert(self):
		self.full_name = get_fullname(self.user)
		self.date = now()

	def validate(self):
		self.set_status()
		set_timeline_doc(self)
		self.set_ip_address()

	def set_status(self):
		if not self.is_new():
			return

		if self.reference_doctype and self.reference_name:
			self.status = "Linked"

	def set_ip_address(self):
		if self.operation in ("Login", "Logout"):
			self.ip_address = saashq.local.request_ip

	@staticmethod
	def clear_old_logs(days=None):
		if not days:
			days = 90
		doctype = DocType("Activity Log")
		saashq.db.delete(doctype, filters=(doctype.creation < (Now() - Interval(days=days))))


def on_doctype_update():
	"""Add indexes in `tabActivity Log`"""
	saashq.db.add_index("Activity Log", ["reference_doctype", "reference_name"])
	saashq.db.add_index("Activity Log", ["timeline_doctype", "timeline_name"])


def add_authentication_log(subject, user, operation="Login", status="Success"):
	saashq.get_doc(
		{
			"doctype": "Activity Log",
			"user": user,
			"status": status,
			"subject": subject,
			"operation": operation,
		}
	).insert(ignore_permissions=True, ignore_links=True)
