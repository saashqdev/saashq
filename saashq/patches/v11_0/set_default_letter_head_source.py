import saashq


def execute():
	saashq.reload_doctype("Letter Head")

	# source of all existing letter heads must be HTML
	saashq.db.sql("update `tabLetter Head` set source = 'HTML'")
