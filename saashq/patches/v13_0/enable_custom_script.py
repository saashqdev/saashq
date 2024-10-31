# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq


def execute():
	"""Enable all the existing Client script"""

	saashq.db.sql(
		"""
		UPDATE `tabClient Script` SET enabled=1
	"""
	)
