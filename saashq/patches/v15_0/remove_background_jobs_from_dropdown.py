import saashq


def execute():
	item = saashq.db.exists("Navbar Item", {"item_label": "Background Jobs"})
	if not item:
		return

	saashq.delete_doc("Navbar Item", item)
