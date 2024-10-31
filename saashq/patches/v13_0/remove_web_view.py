import saashq


def execute():
	saashq.delete_doc_if_exists("DocType", "Web View")
	saashq.delete_doc_if_exists("DocType", "Web View Component")
	saashq.delete_doc_if_exists("DocType", "CSS Class")
