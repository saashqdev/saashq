import saashq


def execute():
	if saashq.db.table_exists("Prepared Report"):
		saashq.reload_doc("core", "doctype", "prepared_report")
		prepared_reports = saashq.get_all("Prepared Report")
		for report in prepared_reports:
			saashq.delete_doc("Prepared Report", report.name)
