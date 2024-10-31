import saashq


def execute():
	if "event_streaming" in saashq.get_installed_apps():
		return

	saashq.delete_doc_if_exists("Module Def", "Event Streaming", force=True)

	for doc in [
		"Event Consumer Document Type",
		"Document Type Mapping",
		"Event Producer",
		"Event Producer Last Update",
		"Event Producer Document Type",
		"Event Consumer",
		"Document Type Field Mapping",
		"Event Update Log",
		"Event Update Log Consumer",
		"Event Sync Log",
	]:
		saashq.delete_doc_if_exists("DocType", doc, force=True)
