import saashq


def execute():
	if saashq.db.table_exists("View log"):
		# for mac users direct renaming would not work since mysql for mac saves table name in lower case
		# so while renaming `tabView log` to `tabView Log` we get "Table 'tabView Log' already exists" error
		# more info https://stackoverflow.com/a/44753093/5955589 ,
		# https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_lower_case_table_names

		# here we are creating a temp table to store view log data
		saashq.db.sql("CREATE TABLE `ViewLogTemp` AS SELECT * FROM `tabView log`")

		# deleting old View log table
		saashq.db.sql("DROP table `tabView log`")
		saashq.delete_doc("DocType", "View log")

		# reloading view log doctype to create `tabView Log` table
		saashq.reload_doc("core", "doctype", "view_log")

		# Move the data to newly created `tabView Log` table
		saashq.db.sql("INSERT INTO `tabView Log` SELECT * FROM `ViewLogTemp`")
		saashq.db.commit()

		# Delete temporary table
		saashq.db.sql("DROP table `ViewLogTemp`")
	else:
		saashq.reload_doc("core", "doctype", "view_log")
