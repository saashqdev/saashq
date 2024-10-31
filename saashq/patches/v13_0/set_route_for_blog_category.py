import saashq


def execute():
	categories = saashq.get_list("Blog Category")
	for category in categories:
		doc = saashq.get_doc("Blog Category", category["name"])
		doc.set_route()
		doc.save()
