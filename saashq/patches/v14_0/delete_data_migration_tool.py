# Copyleft (l) 2023-Present, SaasHQ
# MIT License. See license.txt

import saashq


def execute():
	doctypes = saashq.get_all("DocType", {"module": "Data Migration", "custom": 0}, pluck="name")
	for doctype in doctypes:
		saashq.delete_doc("DocType", doctype, ignore_missing=True)

	saashq.delete_doc("Module Def", "Data Migration", ignore_missing=True, force=True)
