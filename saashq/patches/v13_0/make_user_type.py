import saashq
from saashq.utils.install import create_user_type


def execute():
	saashq.reload_doc("core", "doctype", "role")
	saashq.reload_doc("core", "doctype", "user_document_type")
	saashq.reload_doc("core", "doctype", "user_type_module")
	saashq.reload_doc("core", "doctype", "user_select_document_type")
	saashq.reload_doc("core", "doctype", "user_type")

	create_user_type()
