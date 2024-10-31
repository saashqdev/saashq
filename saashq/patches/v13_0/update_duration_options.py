# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq


def execute():
	saashq.reload_doc("core", "doctype", "DocField")

	if saashq.db.has_column("DocField", "show_days"):
		saashq.db.sql(
			"""
			UPDATE
				tabDocField
			SET
				hide_days = 1 WHERE show_days = 0
		"""
		)
		saashq.db.sql_ddl("alter table tabDocField drop column show_days")

	if saashq.db.has_column("DocField", "show_seconds"):
		saashq.db.sql(
			"""
			UPDATE
				tabDocField
			SET
				hide_seconds = 1 WHERE show_seconds = 0
		"""
		)
		saashq.db.sql_ddl("alter table tabDocField drop column show_seconds")

	saashq.clear_cache(doctype="DocField")
