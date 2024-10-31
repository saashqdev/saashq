import saashq
from saashq.model.rename_doc import rename_doc


def execute():
	if saashq.db.table_exists("Email Alert Recipient") and not saashq.db.table_exists(
		"Notification Recipient"
	):
		rename_doc("DocType", "Email Alert Recipient", "Notification Recipient")
		saashq.reload_doc("email", "doctype", "notification_recipient")

	if saashq.db.table_exists("Email Alert") and not saashq.db.table_exists("Notification"):
		rename_doc("DocType", "Email Alert", "Notification")
		saashq.reload_doc("email", "doctype", "notification")
