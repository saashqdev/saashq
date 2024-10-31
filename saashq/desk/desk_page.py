# Copyright (c) 2015, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import saashq


@saashq.whitelist()
def get(name):
	"""
	Return the :term:`doclist` of the `Page` specified by `name`
	"""
	page = saashq.get_doc("Page", name)
	if page.is_permitted():
		page.load_assets()
		docs = saashq._dict(page.as_dict())
		if getattr(page, "_dynamic_page", None):
			docs["_dynamic_page"] = 1

		return docs
	else:
		saashq.response["403"] = 1
		raise saashq.PermissionError("No read permission for Page %s" % (page.title or name))


@saashq.whitelist(allow_guest=True)
def getpage():
	"""
	Load the page from `saashq.form` and send it via `saashq.response`
	"""
	page = saashq.form_dict.get("name")
	doc = get(page)

	saashq.response.docs.append(doc)
