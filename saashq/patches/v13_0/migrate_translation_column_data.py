import saashq


def execute():
	saashq.reload_doctype("Translation")
	saashq.db.sql(
		"UPDATE `tabTranslation` SET `translated_text`=`target_name`, `source_text`=`source_name`, `contributed`=0"
	)
