import saashq


def execute():
	column = "apply_user_permissions"
	to_remove = ["DocPerm", "Custom DocPerm"]

	for doctype in to_remove:
		if saashq.db.table_exists(doctype):
			if column in saashq.db.get_table_columns(doctype):
				saashq.db.sql(f"alter table `tab{doctype}` drop column {column}")

	saashq.reload_doc("core", "doctype", "docperm", force=True)
	saashq.reload_doc("core", "doctype", "custom_docperm", force=True)
