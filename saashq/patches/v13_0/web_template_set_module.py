# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq


def execute():
	"""Set default module for standard Web Template, if none."""
	saashq.reload_doc("website", "doctype", "Web Template Field")
	saashq.reload_doc("website", "doctype", "web_template")

	standard_templates = saashq.get_list("Web Template", {"standard": 1})
	for template in standard_templates:
		doc = saashq.get_doc("Web Template", template.name)
		if not doc.module:
			doc.module = "Website"
			doc.save()
