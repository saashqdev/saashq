import json

from werkzeug.routing import Rule

import saashq
from saashq import _
from saashq.utils.data import sbool


def document_list(doctype: str):
	if saashq.form_dict.get("fields"):
		saashq.form_dict["fields"] = json.loads(saashq.form_dict["fields"])

	# set limit of records for saashq.get_list
	saashq.form_dict.setdefault(
		"limit_page_length",
		saashq.form_dict.limit or saashq.form_dict.limit_page_length or 20,
	)

	# convert strings to native types - only as_dict and debug accept bool
	for param in ["as_dict", "debug"]:
		param_val = saashq.form_dict.get(param)
		if param_val is not None:
			saashq.form_dict[param] = sbool(param_val)

	# evaluate saashq.get_list
	return saashq.call(saashq.client.get_list, doctype, **saashq.form_dict)


def handle_rpc_call(method: str):
	import saashq.handler

	method = method.split("/")[0]  # for backward compatiblity

	saashq.form_dict.cmd = method
	return saashq.handler.handle()


def create_doc(doctype: str):
	data = get_request_form_data()
	data.pop("doctype", None)
	return saashq.new_doc(doctype, **data).insert()


def update_doc(doctype: str, name: str):
	data = get_request_form_data()

	doc = saashq.get_doc(doctype, name, for_update=True)
	if "flags" in data:
		del data["flags"]

	doc.update(data)
	doc.save()

	# check for child table doctype
	if doc.get("parenttype"):
		saashq.get_doc(doc.parenttype, doc.parent).save()

	return doc


def delete_doc(doctype: str, name: str):
	# TODO: child doc handling
	saashq.delete_doc(doctype, name, ignore_missing=False)
	saashq.response.http_status_code = 202
	return "ok"


def read_doc(doctype: str, name: str):
	# Backward compatiblity
	if "run_method" in saashq.form_dict:
		return execute_doc_method(doctype, name)

	doc = saashq.get_doc(doctype, name)
	if not doc.has_permission("read"):
		raise saashq.PermissionError
	doc.apply_fieldlevel_read_permissions()
	return doc


def execute_doc_method(doctype: str, name: str, method: str | None = None):
	method = method or saashq.form_dict.pop("run_method")
	doc = saashq.get_doc(doctype, name)
	doc.is_whitelisted(method)

	if saashq.request.method == "GET":
		if not doc.has_permission("read"):
			saashq.throw(_("Not permitted"), saashq.PermissionError)
		return doc.run_method(method, **saashq.form_dict)

	elif saashq.request.method == "POST":
		if not doc.has_permission("write"):
			saashq.throw(_("Not permitted"), saashq.PermissionError)

		return doc.run_method(method, **saashq.form_dict)


def get_request_form_data():
	if saashq.form_dict.data is None:
		data = saashq.safe_decode(saashq.request.get_data())
	else:
		data = saashq.form_dict.data

	try:
		return saashq.parse_json(data)
	except ValueError:
		return saashq.form_dict


url_rules = [
	Rule("/method/<path:method>", endpoint=handle_rpc_call),
	Rule("/resource/<doctype>", methods=["GET"], endpoint=document_list),
	Rule("/resource/<doctype>", methods=["POST"], endpoint=create_doc),
	Rule("/resource/<doctype>/<path:name>/", methods=["GET"], endpoint=read_doc),
	Rule("/resource/<doctype>/<path:name>/", methods=["PUT"], endpoint=update_doc),
	Rule("/resource/<doctype>/<path:name>/", methods=["DELETE"], endpoint=delete_doc),
	Rule("/resource/<doctype>/<path:name>/", methods=["POST"], endpoint=execute_doc_method),
]
