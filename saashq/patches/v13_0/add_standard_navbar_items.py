import saashq
from saashq.utils.install import add_standard_navbar_items


def execute():
	# Add standard navbar items for ERPNexus in Navbar Settings
	saashq.reload_doc("core", "doctype", "navbar_settings")
	saashq.reload_doc("core", "doctype", "navbar_item")
	add_standard_navbar_items()
