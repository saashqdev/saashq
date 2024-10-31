# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq


def execute():
	saashq.delete_doc_if_exists("DocType", "User Permission for Page and Report")
