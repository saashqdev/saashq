# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq
from saashq.model import is_default_field
from saashq.query_builder import Order
from saashq.query_builder.functions import Count
from saashq.query_builder.terms import SubQuery
from saashq.query_builder.utils import DocType


@saashq.whitelist()
def get_list_settings(doctype):
	try:
		return saashq.get_cached_doc("List View Settings", doctype)
	except saashq.DoesNotExistError:
		saashq.clear_messages()


@saashq.whitelist()
def set_list_settings(doctype, values):
	try:
		doc = saashq.get_doc("List View Settings", doctype)
	except saashq.DoesNotExistError:
		doc = saashq.new_doc("List View Settings")
		doc.name = doctype
		saashq.clear_messages()
	doc.update(saashq.parse_json(values))
	doc.save()


@saashq.whitelist()
def get_group_by_count(doctype: str, current_filters: str, field: str) -> list[dict]:
	current_filters = saashq.parse_json(current_filters)

	if field == "assigned_to":
		ToDo = DocType("ToDo")
		User = DocType("User")
		count = Count("*").as_("count")
		filtered_records = saashq.qb.get_query(
			doctype,
			filters=current_filters,
			fields=["name"],
			validate_filters=True,
		)

		return (
			saashq.qb.from_(ToDo)
			.from_(User)
			.select(ToDo.allocated_to.as_("name"), count)
			.where(
				(ToDo.status != "Cancelled")
				& (ToDo.allocated_to == User.name)
				& (User.user_type == "System User")
				& (ToDo.reference_name.isin(SubQuery(filtered_records)))
			)
			.groupby(ToDo.allocated_to)
			.orderby(count, order=Order.desc)
			.limit(50)
			.run(as_dict=True)
		)

	meta = saashq.get_meta(doctype)

	if not meta.has_field(field) and not is_default_field(field):
		raise ValueError("Field does not belong to doctype")

	data = saashq.get_list(
		doctype,
		filters=current_filters,
		group_by=f"`tab{doctype}`.{field}",
		fields=["count(*) as count", f"`{field}` as name"],
		order_by="count desc",
		limit=50,
	)

	# Add in title if it's a link field and `show_title_field_in_link` is set
	if (field_meta := meta.get_field(field)) and field_meta.fieldtype == "Link":
		link_meta = saashq.get_meta(field_meta.options)
		if link_meta.show_title_field_in_link:
			title_field = link_meta.get_title_field()
			for item in data:
				item.title = saashq.get_value(field_meta.options, item.name, title_field)

	return data
