import saashq
from saashq.model.rename_doc import rename_doc


def execute():
	if saashq.db.exists("DocType", "Client Script"):
		return

	saashq.flags.ignore_route_conflict_validation = True
	rename_doc("DocType", "Custom Script", "Client Script")
	saashq.flags.ignore_route_conflict_validation = False

	saashq.reload_doctype("Client Script", force=True)
