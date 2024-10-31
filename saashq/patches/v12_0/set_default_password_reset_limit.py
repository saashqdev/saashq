# Copyright (c) 2015, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import saashq


def execute():
	saashq.reload_doc("core", "doctype", "system_settings", force=1)
	saashq.db.set_single_value("System Settings", "password_reset_limit", 3)
