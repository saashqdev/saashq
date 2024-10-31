import saashq


def execute():
	saashq.db.delete("DocType", {"name": "Feedback Request"})
