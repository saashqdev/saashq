import saashq


def execute():
	saashq.db.sql(
		"""UPDATE `tabUser Permission`
		SET `modified`=NOW(), `creation`=NOW()
		WHERE `creation` IS NULL"""
	)
