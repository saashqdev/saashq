import saashq
from saashq.model import no_value_fields, table_fields


@saashq.whitelist()
def get_preview_data(doctype, docname):
	preview_fields = []
	meta = saashq.get_meta(doctype)
	if not meta.show_preview_popup:
		return

	preview_fields = [
		field.fieldname
		for field in meta.fields
		if field.in_preview and field.fieldtype not in no_value_fields and field.fieldtype not in table_fields
	]

	# no preview fields defined, build list from mandatory fields
	if not preview_fields:
		preview_fields = [
			field.fieldname for field in meta.fields if field.reqd and field.fieldtype not in table_fields
		]

	title_field = meta.get_title_field()
	image_field = meta.image_field

	preview_fields.append(title_field)
	preview_fields.append(image_field)
	preview_fields.append("name")

	preview_data = saashq.get_list(doctype, filters={"name": docname}, fields=preview_fields, limit=1)

	if not preview_data:
		return

	preview_data = preview_data[0]

	formatted_preview_data = {
		"preview_image": preview_data.get(image_field),
		"preview_title": preview_data.get(title_field),
		"name": preview_data.get("name"),
	}

	for key, val in preview_data.items():
		if val and meta.has_field(key) and key not in [image_field, title_field, "name"]:
			formatted_preview_data[meta.get_field(key).label] = saashq.format(
				val,
				meta.get_field(key).fieldtype,
				translated=True,
			)

	return formatted_preview_data
