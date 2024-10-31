"""REST API v2

This file defines routes and implementation for REST API.

Note:
	- All functions in this file should be treated as "whitelisted" as they are exposed via routes
	- None of the functions present here should be called from python code, their location and
	  internal implementation can change without treating it as "breaking change".
"""
import json
from typing import Any

from werkzeug.routing import Rule

import saashq
import saashq.client
from saashq import _, get_newargs, is_whitelisted
from saashq.core.doctype.server_script.server_script_utils import get_server_script_map
from saashq.handler import is_valid_http_method, run_server_script, upload_file

PERMISSION_MAP = {
	"GET": "read",
	"POST": "write",
}


def handle_rpc_call(method: str, doctype: str | None = None):
	from saashq.modules.utils import load_doctype_module

	if doctype:
		# Expand to run actual method from doctype controller
		module = load_doctype_module(doctype)
		method = module.__name__ + "." + method

	for hook in reversed(saashq.get_hooks("override_whitelisted_methods", {}).get(method, [])):
		# override using the last hook
		method = hook
		break

	# via server script
	server_script = get_server_script_map().get("_api", {}).get(method)
	if server_script:
		return run_server_script(server_script)

	try:
		method = saashq.get_attr(method)
	except Exception as e:
		saashq.throw(_("Failed to get method {0} with {1}").format(method, e))

	is_whitelisted(method)
	is_valid_http_method(method)

	return saashq.call(method, **saashq.form_dict)


def login():
	"""Login happens implicitly, this function doesn't do anything."""
	pass


def logout():
	saashq.local.login_manager.logout()
	saashq.db.commit()


def read_doc(doctype: str, name: str):
	doc = saashq.get_doc(doctype, name)
	doc.check_permission("read")
	doc.apply_fieldlevel_read_permissions()
	return doc


def document_list(doctype: str):
	if saashq.form_dict.get("fields"):
		saashq.form_dict["fields"] = json.loads(saashq.form_dict["fields"])

	# set limit of records for saashq.get_list
	saashq.form_dict.limit_page_length = saashq.form_dict.limit or 20
	# evaluate saashq.get_list
	return saashq.call(saashq.client.get_list, doctype, **saashq.form_dict)


def count(doctype: str) -> int:
	from saashq.desk.reportview import get_count

	saashq.form_dict.doctype = doctype

	return get_count()


def create_doc(doctype: str):
	data = saashq.form_dict
	data.pop("doctype", None)
	return saashq.new_doc(doctype, **data).insert()


def update_doc(doctype: str, name: str):
	data = saashq.form_dict

	doc = saashq.get_doc(doctype, name, for_update=True)
	data.pop("flags", None)
	doc.update(data)
	doc.save()

	# check for child table doctype
	if doc.get("parenttype"):
		saashq.get_doc(doc.parenttype, doc.parent).save()

	return doc


def delete_doc(doctype: str, name: str):
	saashq.client.delete_doc(doctype, name)
	saashq.response.http_status_code = 202
	return "ok"


def get_meta(doctype: str):
	saashq.only_for("All")
	return saashq.get_meta(doctype)


def execute_doc_method(doctype: str, name: str, method: str | None = None):
	"""Get a document from DB and execute method on it.

	Use cases:
	- Submitting/cancelling document
	- Triggering some kind of update on a document
	"""
	method = method or saashq.form_dict.pop("run_method")
	doc = saashq.get_doc(doctype, name)
	doc.is_whitelisted(method)

	doc.check_permission(PERMISSION_MAP[saashq.request.method])
	return doc.run_method(method, **saashq.form_dict)


def run_doc_method(method: str, document: dict[str, Any] | str, kwargs=None):
	"""run a whitelisted controller method on in-memory document.


	This is useful for building clients that don't necessarily encode all the business logic but
	call server side function on object to validate and modify the doc.

	The doc CAN exists in DB too and can write to DB as well if method is POST.
	"""

	if isinstance(document, str):
		document = saashq.parse_json(document)

	if kwargs is None:
		kwargs = {}

	doc = saashq.get_doc(document)
	doc._original_modified = doc.modified
	doc.check_if_latest()

	doc.check_permission(PERMISSION_MAP[saashq.request.method])

	method_obj = getattr(doc, method)
	fn = getattr(method_obj, "__func__", method_obj)
	is_whitelisted(fn)
	is_valid_http_method(fn)

	new_kwargs = get_newargs(fn, kwargs)
	response = doc.run_method(method, **new_kwargs)
	saashq.response.docs.append(doc)  # send modified document and result both.
	return response


url_rules = [
	# RPC calls
	Rule("/method/login", endpoint=login),
	Rule("/method/logout", endpoint=logout),
	Rule("/method/ping", endpoint=saashq.ping),
	Rule("/method/upload_file", endpoint=upload_file),
	Rule("/method/<method>", endpoint=handle_rpc_call),
	Rule(
		"/method/run_doc_method",
		methods=["GET", "POST"],
		endpoint=lambda: saashq.call(run_doc_method, **saashq.form_dict),
	),
	Rule("/method/<doctype>/<method>", endpoint=handle_rpc_call),
	# Document level APIs
	Rule("/document/<doctype>", methods=["GET"], endpoint=document_list),
	Rule("/document/<doctype>", methods=["POST"], endpoint=create_doc),
	Rule("/document/<doctype>/<path:name>/", methods=["GET"], endpoint=read_doc),
	Rule("/document/<doctype>/<path:name>/", methods=["PATCH", "PUT"], endpoint=update_doc),
	Rule("/document/<doctype>/<path:name>/", methods=["DELETE"], endpoint=delete_doc),
	Rule(
		"/document/<doctype>/<path:name>/method/<method>/",
		methods=["GET", "POST"],
		endpoint=execute_doc_method,
	),
	# Collection level APIs
	Rule("/doctype/<doctype>/meta", methods=["GET"], endpoint=get_meta),
	Rule("/doctype/<doctype>/count", methods=["GET"], endpoint=count),
]
