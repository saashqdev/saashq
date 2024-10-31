import re

import saashq
from saashq.core.doctype.user.user import create_contact


def execute():
	"""Create Contact for each User if not present"""
	saashq.reload_doc("integrations", "doctype", "google_contacts")
	saashq.reload_doc("contacts", "doctype", "contact")
	saashq.reload_doc("core", "doctype", "dynamic_link")

	contact_meta = saashq.get_meta("Contact")
	if contact_meta.has_field("phone_nos") and contact_meta.has_field("email_ids"):
		saashq.reload_doc("contacts", "doctype", "contact_phone")
		saashq.reload_doc("contacts", "doctype", "contact_email")

	users = saashq.get_all("User", filters={"name": ("not in", "Administrator, Guest")}, fields=["*"])
	for user in users:
		if saashq.db.exists("Contact", {"email_id": user.email}) or saashq.db.exists(
			"Contact Email", {"email_id": user.email}
		):
			continue
		if user.first_name:
			user.first_name = re.sub("[<>]+", "", saashq.safe_decode(user.first_name))
		if user.last_name:
			user.last_name = re.sub("[<>]+", "", saashq.safe_decode(user.last_name))
		create_contact(user, ignore_links=True, ignore_mandatory=True)
