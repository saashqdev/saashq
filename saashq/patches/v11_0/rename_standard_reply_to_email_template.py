import saashq
from saashq.model.rename_doc import rename_doc


def execute():
	if saashq.db.table_exists("Standard Reply") and not saashq.db.table_exists("Email Template"):
		rename_doc("DocType", "Standard Reply", "Email Template")
		saashq.reload_doc("email", "doctype", "email_template")
