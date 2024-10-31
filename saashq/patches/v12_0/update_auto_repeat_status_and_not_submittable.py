import saashq
from saashq.custom.doctype.custom_field.custom_field import create_custom_field


def execute():
	# auto repeat is not submittable in v12
	saashq.reload_doc("automation", "doctype", "Auto Repeat")
	saashq.db.sql("update `tabDocPerm` set submit=0, cancel=0, amend=0 where parent='Auto Repeat'")
	saashq.db.sql("update `tabAuto Repeat` set docstatus=0 where docstatus=1 or docstatus=2")

	for entry in saashq.get_all("Auto Repeat"):
		doc = saashq.get_doc("Auto Repeat", entry.name)

		# create custom field for allow auto repeat
		fields = saashq.get_meta(doc.reference_doctype).fields
		insert_after = fields[len(fields) - 1].fieldname
		df = dict(
			fieldname="auto_repeat",
			label="Auto Repeat",
			fieldtype="Link",
			insert_after=insert_after,
			options="Auto Repeat",
			hidden=1,
			print_hide=1,
			read_only=1,
		)
		create_custom_field(doc.reference_doctype, df)

		if doc.status in ["Draft", "Stopped", "Cancelled"]:
			doc.disabled = 1

		doc.flags.ignore_links = 1
		# updates current status as Active, Disabled or Completed on validate
		doc.save()
