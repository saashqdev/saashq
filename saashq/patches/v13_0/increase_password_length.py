import saashq


def execute():
	saashq.db.change_column_type("__Auth", column="password", type="TEXT")
