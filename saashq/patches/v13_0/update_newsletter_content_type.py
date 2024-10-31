# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq


def execute():
	saashq.reload_doc("email", "doctype", "Newsletter")
	saashq.db.sql(
		"""
		UPDATE tabNewsletter
		SET content_type = 'Rich Text'
	"""
	)
