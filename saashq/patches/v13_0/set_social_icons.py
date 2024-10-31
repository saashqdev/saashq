import saashq


def execute():
	providers = saashq.get_all("Social Login Key")

	for provider in providers:
		doc = saashq.get_doc("Social Login Key", provider)
		doc.set_icon()
		doc.save()
