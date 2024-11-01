# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq


def execute():
	if not saashq.db.table_exists("Data Import"):
		return

	meta = saashq.get_meta("Data Import")
	# if Data Import is the new one, return early
	if meta.fields[1].fieldname == "import_type":
		return

	saashq.db.sql("DROP TABLE IF EXISTS `tabData Import Legacy`")
	saashq.rename_doc("DocType", "Data Import", "Data Import Legacy")
	saashq.db.commit()
	saashq.db.sql("DROP TABLE IF EXISTS `tabData Import`")
	saashq.rename_doc("DocType", "Data Import Beta", "Data Import")
