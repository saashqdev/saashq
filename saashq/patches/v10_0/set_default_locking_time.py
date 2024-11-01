# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq


def execute():
	saashq.reload_doc("core", "doctype", "system_settings")
	saashq.db.set_single_value("System Settings", "allow_login_after_fail", 60)
