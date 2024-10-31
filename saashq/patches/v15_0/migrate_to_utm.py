import saashq


def execute():
	"""
	Rename the Marketing Campaign table to UTM Campaign table
	"""
	if saashq.db.exists("DocType", "UTM Campaign"):
		return
	saashq.rename_doc("DocType", "Marketing Campaign", "UTM Campaign", force=True)
	saashq.reload_doctype("UTM Campaign", force=True)
