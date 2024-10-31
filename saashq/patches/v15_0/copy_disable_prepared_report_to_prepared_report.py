import saashq


def execute():
	table = saashq.qb.DocType("Report")
	saashq.qb.update(table).set(table.prepared_report, 0).where(table.disable_prepared_report == 1)
