# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import json

import saashq
from saashq import _


@saashq.whitelist()
def update_event(args, field_map):
	"""Updates Event (called via calendar) based on passed `field_map`"""
	args = saashq._dict(json.loads(args))
	field_map = saashq._dict(json.loads(field_map))
	w = saashq.get_doc(args.doctype, args.name)
	w.set(field_map.start, args[field_map.start])
	w.set(field_map.end, args.get(field_map.end))
	w.save()


def get_event_conditions(doctype, filters=None):
	"""Return SQL conditions with user permissions and filters for event queries."""
	from saashq.desk.reportview import get_filters_cond

	if not saashq.has_permission(doctype):
		saashq.throw(_("Not Permitted"), saashq.PermissionError)

	return get_filters_cond(doctype, filters, [], with_match_conditions=True)


@saashq.whitelist()
def get_events(doctype, start, end, field_map, filters=None, fields=None):
	field_map = saashq._dict(json.loads(field_map))
	fields = saashq.parse_json(fields)

	doc_meta = saashq.get_meta(doctype)
	for d in doc_meta.fields:
		if d.fieldtype == "Color":
			field_map.update({"color": d.fieldname})

	filters = json.loads(filters) if filters else []

	if not fields:
		fields = [field_map.start, field_map.end, field_map.title, "name"]

	if field_map.color:
		fields.append(field_map.color)

	start_date = "ifnull(%s, '0001-01-01 00:00:00')" % field_map.start
	end_date = "ifnull(%s, '2199-12-31 00:00:00')" % field_map.end

	filters += [
		[doctype, start_date, "<=", end],
		[doctype, end_date, ">=", start],
	]
	fields = list({field for field in fields if field})
	return saashq.get_list(doctype, fields=fields, filters=filters)
