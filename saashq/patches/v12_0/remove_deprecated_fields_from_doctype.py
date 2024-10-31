import saashq


def execute():
	saashq.reload_doc("core", "doctype", "doctype_link")
	saashq.reload_doc("core", "doctype", "doctype_action")
	saashq.reload_doc("core", "doctype", "doctype")
	saashq.model.delete_fields({"DocType": ["hide_heading", "image_view", "read_only_onload"]}, delete=1)

	saashq.db.delete("Property Setter", {"property": "read_only_onload"})
