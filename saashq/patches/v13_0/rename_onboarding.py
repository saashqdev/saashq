# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq


def execute():
	if saashq.db.exists("DocType", "Onboarding"):
		saashq.rename_doc("DocType", "Onboarding", "Module Onboarding", ignore_if_exists=True)
