import click

import saashq


def execute():
	doctype = "Data Import Legacy"
	table = saashq.utils.get_table_name(doctype)

	# delete the doctype record to avoid broken links
	saashq.delete_doc("DocType", doctype, force=True)

	# leaving table in database for manual cleanup
	click.secho(
		f"`{doctype}` has been deprecated. The DocType is deleted, but the data still"
		" exists on the database. If this data is worth recovering, you may export it"
		f" using\n\n\twrench --site {saashq.local.site} backup -i '{doctype}'\n\nAfter"
		" this, the table will continue to persist in the database, until you choose"
		" to remove it yourself. If you want to drop the table, you may run\n\n\twrench"
		f" --site {saashq.local.site} execute saashq.db.sql --args \"('DROP TABLE IF"
		f" EXISTS `{table}`', )\"\n",
		fg="yellow",
	)
