import saashq


def execute():
	for name in ("desktop", "space"):
		saashq.delete_doc("Page", name)
