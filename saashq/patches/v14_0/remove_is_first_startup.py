import saashq


def execute():
	singles = saashq.qb.Table("tabSingles")
	saashq.qb.from_(singles).delete().where(
		(singles.doctype == "System Settings") & (singles.field == "is_first_startup")
	).run()
