# Copyright (c) 2020, Saashq Technologies Pvt. Ltd. and Contributors
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
