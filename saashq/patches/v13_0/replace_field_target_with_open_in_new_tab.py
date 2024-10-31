import saashq


def execute():
	doctype = "Top Bar Item"
	if not saashq.db.table_exists(doctype) or not saashq.db.has_column(doctype, "target"):
		return

	saashq.reload_doc("website", "doctype", "top_bar_item")
	saashq.db.set_value(doctype, {"target": 'target = "_blank"'}, "open_in_new_tab", 1)
