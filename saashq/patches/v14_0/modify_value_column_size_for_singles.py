import saashq


def execute():
	if saashq.db.db_type == "mariadb":
		saashq.db.sql_ddl("alter table `tabSingles` modify column `value` longtext")
