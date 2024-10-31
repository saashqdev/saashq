# Copyright (c) 2020, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import saashq


def execute():
	if saashq.db.exists("DocType", "Onboarding"):
		saashq.rename_doc("DocType", "Onboarding", "Module Onboarding", ignore_if_exists=True)
