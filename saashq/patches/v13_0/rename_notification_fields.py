# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq
from saashq.model.utils.rename_field import rename_field


def execute():
	"""
	Change notification recipient fields from email to receiver fields
	"""
	saashq.reload_doc("Email", "doctype", "Notification Recipient")
	saashq.reload_doc("Email", "doctype", "Notification")

	rename_field("Notification Recipient", "email_by_document_field", "receiver_by_document_field")
	rename_field("Notification Recipient", "email_by_role", "receiver_by_role")
