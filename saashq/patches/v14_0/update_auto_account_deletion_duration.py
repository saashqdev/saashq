import saashq


def execute():
	days = saashq.db.get_single_value("Website Settings", "auto_account_deletion")
	saashq.db.set_single_value("Website Settings", "auto_account_deletion", days * 24)
