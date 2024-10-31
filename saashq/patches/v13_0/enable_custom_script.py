# Copyright (c) 2020, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import saashq


def execute():
	"""Enable all the existing Client script"""

	saashq.db.sql(
		"""
		UPDATE `tabClient Script` SET enabled=1
	"""
	)
