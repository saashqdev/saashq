# Copyright (c) 2023-Present, SaasHQ
# MIT License. See license.txt


import saashq


def execute():
	saashq.reload_doc("website", "doctype", "web_form_list_column")
	saashq.reload_doctype("Web Form")

	for web_form in saashq.get_all("Web Form", fields=["*"]):
		if web_form.allow_multiple and not web_form.show_list:
			saashq.db.set_value("Web Form", web_form.name, "show_list", True)
