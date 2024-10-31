import saashq


def execute():
	saashq.reload_doc("core", "doctype", "user")
	saashq.db.sql(
		"""
		UPDATE `tabUser`
		SET `home_settings` = ''
		WHERE `user_type` = 'System User'
	"""
	)
