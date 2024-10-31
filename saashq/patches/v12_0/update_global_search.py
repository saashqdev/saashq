import saashq
from saashq.desk.page.setup_wizard.install_fixtures import update_global_search_doctypes


def execute():
	saashq.reload_doc("desk", "doctype", "global_search_doctype")
	saashq.reload_doc("desk", "doctype", "global_search_settings")
	update_global_search_doctypes()
