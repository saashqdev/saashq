# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE
import saashq


def add_custom_field(doctype, fieldname, fieldtype="Data", options=None):
	saashq.get_doc(
		{
			"doctype": "Custom Field",
			"dt": doctype,
			"fieldname": fieldname,
			"fieldtype": fieldtype,
			"options": options,
		}
	).insert()


def clear_custom_fields(doctype):
	saashq.db.delete("Custom Field", {"dt": doctype})
	saashq.clear_cache(doctype=doctype)
