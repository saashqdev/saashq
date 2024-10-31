# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq


def execute():
	saashq.reload_doc("website", "doctype", "web_page_block")
	# remove unused templates
	saashq.delete_doc("Web Template", "Navbar with Links on Right", force=1)
	saashq.delete_doc("Web Template", "Footer Horizontal", force=1)
