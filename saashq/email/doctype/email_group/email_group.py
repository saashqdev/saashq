# Copyleft (l) 2023-Present, Saashq Technologies and contributors
# License: MIT. See LICENSE

import contextlib

import saashq
from saashq import _
from saashq.model.document import Document
from saashq.utils import parse_addr, validate_email_address


class EmailGroup(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		add_query_parameters: DF.Check
		confirmation_email_template: DF.Link | None
		title: DF.Data
		total_subscribers: DF.Int
		welcome_email_template: DF.Link | None
		welcome_url: DF.Data | None
	# end: auto-generated types

	def onload(self):
		singles = [d.name for d in saashq.get_all("DocType", "name", {"issingle": 1})]
		self.get("__onload").import_types = [
			{"value": d.parent, "label": f"{d.parent} ({d.label})"}
			for d in saashq.get_all("DocField", ("parent", "label"), {"options": "Email"})
			if d.parent not in singles
		]

	def import_from(self, doctype):
		"""Extract Email Addresses from given doctype and add them to the current list"""
		meta = saashq.get_meta(doctype)
		email_field = next(
			d.fieldname
			for d in meta.fields
			if d.fieldtype in ("Data", "Small Text", "Text", "Code") and d.options == "Email"
		)
		unsubscribed_field = "unsubscribed" if meta.get_field("unsubscribed") else None
		added = 0

		for user in saashq.get_all(doctype, [email_field, unsubscribed_field or "name"]):
			with contextlib.suppress(saashq.UniqueValidationError, saashq.InvalidEmailAddressError):
				email = parse_addr(user.get(email_field))[1] if user.get(email_field) else None
				if email:
					saashq.get_doc(
						{
							"doctype": "Email Group Member",
							"email_group": self.name,
							"email": email,
							"unsubscribed": user.get(unsubscribed_field) if unsubscribed_field else 0,
						}
					).insert(ignore_permissions=True)
					added += 1

		saashq.msgprint(_("{0} subscribers added").format(added))

		return self.update_total_subscribers()

	def update_total_subscribers(self):
		self.total_subscribers = self.get_total_subscribers()
		self.db_update()
		return self.total_subscribers

	def get_total_subscribers(self):
		return saashq.db.sql(
			"""select count(*) from `tabEmail Group Member`
			where email_group=%s""",
			self.name,
		)[0][0]

	@saashq.whitelist()
	def preview_welcome_url(self, email: str | None = None) -> str | None:
		"""Get Welcome URL for the email group."""
		return self.get_welcome_url(email)

	def get_welcome_url(self, email: str | None = None) -> str | None:
		"""Get Welcome URL for the email group."""
		if not self.welcome_url:
			return None

		return (
			add_query_params(self.welcome_url, {"email": email, "email_group": self.name})
			if self.add_query_parameters
			else self.welcome_url
		)

	def on_trash(self):
		for d in saashq.get_all("Email Group Member", "name", {"email_group": self.name}):
			saashq.delete_doc("Email Group Member", d.name)


@saashq.whitelist()
def import_from(name, doctype):
	nlist = saashq.get_doc("Email Group", name)
	if nlist.has_permission("write"):
		return nlist.import_from(doctype)


@saashq.whitelist()
def add_subscribers(name, email_list):
	if not isinstance(email_list, list | tuple):
		email_list = email_list.replace(",", "\n").split("\n")

	template = saashq.db.get_value("Email Group", name, "welcome_email_template")
	welcome_email = saashq.get_doc("Email Template", template) if template else None

	count = 0
	for email in email_list:
		email = email.strip()
		parsed_email = validate_email_address(email, False)

		if parsed_email:
			if not saashq.db.get_value("Email Group Member", {"email_group": name, "email": parsed_email}):
				saashq.get_doc(
					{"doctype": "Email Group Member", "email_group": name, "email": parsed_email}
				).insert(ignore_permissions=saashq.flags.ignore_permissions)

				send_welcome_email(welcome_email, parsed_email, name)

				count += 1
			else:
				pass
		else:
			saashq.msgprint(_("{0} is not a valid Email Address").format(email))

	saashq.msgprint(_("{0} subscribers added").format(count))

	return saashq.get_doc("Email Group", name).update_total_subscribers()


def send_welcome_email(welcome_email, email, email_group):
	"""Send welcome email for the subscribers of a given email group."""
	if not welcome_email:
		return

	args = dict(email=email, email_group=email_group)
	message = saashq.render_template(welcome_email.response_, args)
	saashq.sendmail(email, subject=welcome_email.subject, message=message)


def add_query_params(url: str, params: dict) -> str:
	from urllib.parse import urlencode, urlparse, urlunparse

	if not params:
		return url

	query_string = urlencode(params)
	parsed = list(urlparse(url))
	if parsed[4]:
		parsed[4] += f"&{query_string}"
	else:
		parsed[4] = query_string

	return urlunparse(parsed)
