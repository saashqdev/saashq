import saashq


def execute():
	saashq.delete_doc_if_exists("DocType", "Post")
	saashq.delete_doc_if_exists("DocType", "Post Comment")
