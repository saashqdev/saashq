import saashq


def execute():
	saashq.reload_doc("workflow", "doctype", "workflow_transition")
	saashq.db.sql("update `tabWorkflow Transition` set allow_self_approval=1")
