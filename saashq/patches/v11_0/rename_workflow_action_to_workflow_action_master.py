import saashq
from saashq.model.rename_doc import rename_doc


def execute():
	if saashq.db.table_exists("Workflow Action") and not saashq.db.table_exists("Workflow Action Master"):
		rename_doc("DocType", "Workflow Action", "Workflow Action Master")
		saashq.reload_doc("workflow", "doctype", "workflow_action_master")
