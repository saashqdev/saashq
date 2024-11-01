# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import os
from mimetypes import guess_type
from typing import TYPE_CHECKING

from werkzeug.wrappers import Response

import saashq
import saashq.sessions
import saashq.utils
from saashq import _, is_whitelisted, ping
from saashq.core.doctype.server_script.server_script_utils import get_server_script_map
from saashq.monitor import add_data_to_monitor
from saashq.utils import cint
from saashq.utils.csvutils import build_csv_response
from saashq.utils.deprecations import deprecated
from saashq.utils.image import optimize_image
from saashq.utils.response import build_response

if TYPE_CHECKING:
	from saashq.core.doctype.file.file import File
	from saashq.core.doctype.user.user import User

ALLOWED_MIMETYPES = (
	"image/png",
	"image/jpeg",
	"application/pdf",
	"application/msword",
	"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
	"application/vnd.ms-excel",
	"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
	"application/vnd.oasis.opendocument.text",
	"application/vnd.oasis.opendocument.spreadsheet",
	"text/plain",
	"video/quicktime",
	"video/mp4",
)


def handle():
	"""handle request"""

	cmd = saashq.local.form_dict.cmd
	data = None

	if cmd != "login":
		data = execute_cmd(cmd)

	# data can be an empty string or list which are valid responses
	if data is not None:
		if isinstance(data, Response):
			# method returns a response object, pass it on
			return data

		# add the response to `message` label
		saashq.response["message"] = data


def execute_cmd(cmd, from_async=False):
	"""execute a request as python module"""
	for hook in reversed(saashq.get_hooks("override_whitelisted_methods", {}).get(cmd, [])):
		# override using the last hook
		cmd = hook
		break

	# via server script
	server_script = get_server_script_map().get("_api", {}).get(cmd)
	if server_script:
		return run_server_script(server_script)

	try:
		method = get_attr(cmd)
	except Exception as e:
		saashq.throw(_("Failed to get method for command {0} with {1}").format(cmd, e))

	if from_async:
		method = method.queue

	if method != run_doc_method:
		is_whitelisted(method)
		is_valid_http_method(method)

	return saashq.call(method, **saashq.form_dict)


def run_server_script(server_script):
	response = saashq.get_doc("Server Script", server_script).execute_method()

	# some server scripts return output using flags (empty dict by default),
	# while others directly modify saashq.response
	# return flags if not empty dict (this overwrites saashq.response.message)
	if response != {}:
		return response


def is_valid_http_method(method):
	if saashq.flags.in_safe_exec:
		return

	http_method = saashq.local.request.method

	if http_method not in saashq.allowed_http_methods_for_whitelisted_func[method]:
		saashq.throw_permission_error()


@saashq.whitelist(allow_guest=True)
def logout():
	saashq.local.login_manager.logout()
	saashq.db.commit()


@saashq.whitelist(allow_guest=True)
def web_logout():
	saashq.local.login_manager.logout()
	saashq.db.commit()
	saashq.respond_as_web_page(
		_("Logged Out"), _("You have been successfully logged out"), indicator_color="green"
	)


@saashq.whitelist(allow_guest=True)
def upload_file():
	user = None
	if saashq.session.user == "Guest":
		if saashq.get_system_settings("allow_guests_to_upload_files"):
			ignore_permissions = True
		else:
			raise saashq.PermissionError
	else:
		user: "User" = saashq.get_doc("User", saashq.session.user)
		ignore_permissions = False

	files = saashq.request.files
	is_private = saashq.form_dict.is_private
	doctype = saashq.form_dict.doctype
	docname = saashq.form_dict.docname
	fieldname = saashq.form_dict.fieldname
	file_url = saashq.form_dict.file_url
	folder = saashq.form_dict.folder or "Home"
	method = saashq.form_dict.method
	filename = saashq.form_dict.file_name
	optimize = saashq.form_dict.optimize
	content = None

	if library_file := saashq.form_dict.get("library_file_name"):
		saashq.has_permission("File", doc=library_file, throw=True)
		doc = saashq.get_value(
			"File",
			saashq.form_dict.library_file_name,
			["is_private", "file_url", "file_name"],
			as_dict=True,
		)
		is_private = doc.is_private
		file_url = doc.file_url
		filename = doc.file_name

	if not ignore_permissions:
		check_write_permission(doctype, docname)

	if "file" in files:
		file = files["file"]
		content = file.stream.read()
		filename = file.filename

		content_type = guess_type(filename)[0]
		if optimize and content_type and content_type.startswith("image/"):
			args = {"content": content, "content_type": content_type}
			if saashq.form_dict.max_width:
				args["max_width"] = int(saashq.form_dict.max_width)
			if saashq.form_dict.max_height:
				args["max_height"] = int(saashq.form_dict.max_height)
			content = optimize_image(**args)

	saashq.local.uploaded_file_url = file_url
	saashq.local.uploaded_file = content
	saashq.local.uploaded_filename = filename

	if content is not None and (saashq.session.user == "Guest" or (user and not user.has_desk_access())):
		filetype = guess_type(filename)[0]
		if filetype not in ALLOWED_MIMETYPES:
			saashq.throw(_("You can only upload JPG, PNG, PDF, TXT or Microsoft documents."))

	if method:
		method = saashq.get_attr(method)
		is_whitelisted(method)
		return method()
	else:
		return saashq.get_doc(
			{
				"doctype": "File",
				"attached_to_doctype": doctype,
				"attached_to_name": docname,
				"attached_to_field": fieldname,
				"folder": folder,
				"file_name": filename,
				"file_url": file_url,
				"is_private": cint(is_private),
				"content": content,
			}
		).save(ignore_permissions=ignore_permissions)


def check_write_permission(doctype: str | None = None, name: str | None = None):
	check_doctype = doctype and not name
	if doctype and name:
		try:
			doc = saashq.get_doc(doctype, name)
			doc.check_permission("write")
		except saashq.DoesNotExistError:
			# doc has not been inserted yet, name is set to "new-some-doctype"
			# If doc inserts fine then only this attachment will be linked see file/utils.py:relink_mismatched_files
			return

	if check_doctype:
		saashq.has_permission(doctype, "write", throw=True)


@saashq.whitelist(allow_guest=True)
def download_file(file_url: str):
	"""
	Download file using token and REST API. Valid session or
	token is required to download private files.

	Method : GET
	Endpoints : download_file, saashq.core.doctype.file.file.download_file
	URL Params : file_name = /path/to/file relative to site path
	"""
	file: "File" = saashq.get_doc("File", {"file_url": file_url})
	if not file.is_downloadable():
		raise saashq.PermissionError

	saashq.local.response.filename = os.path.basename(file_url)
	saashq.local.response.filecontent = file.get_content()
	saashq.local.response.type = "download"


def get_attr(cmd):
	"""get method object from cmd"""
	if "." in cmd:
		method = saashq.get_attr(cmd)
	else:
		from saashq.deprecation_dumpster import deprecation_warning

		deprecation_warning(
			"unknown",
			"v17",
			f"Calling shorthand for {cmd} is deprecated, please specify full path in RPC call.",
		)
		method = globals()[cmd]
	return method


def run_doc_method(method, docs=None, dt=None, dn=None, arg=None, args=None):
	"""run a whitelisted controller method"""
	from inspect import signature

	if not args and arg:
		args = arg

	if dt:  # not called from a doctype (from a page)
		if not dn:
			dn = dt  # single
		doc = saashq.get_doc(dt, dn)

	else:
		docs = saashq.parse_json(docs)
		doc = saashq.get_doc(docs)
		doc._original_modified = doc.modified
		doc.check_if_latest()

	if not doc or not doc.has_permission("read"):
		saashq.throw_permission_error()

	try:
		args = saashq.parse_json(args)
	except ValueError:
		pass

	method_obj = getattr(doc, method)
	fn = getattr(method_obj, "__func__", method_obj)
	is_whitelisted(fn)
	is_valid_http_method(fn)

	fnargs = list(signature(method_obj).parameters)

	if not fnargs or (len(fnargs) == 1 and fnargs[0] == "self"):
		response = doc.run_method(method)

	elif "args" in fnargs or not isinstance(args, dict):
		response = doc.run_method(method, args)

	else:
		response = doc.run_method(method, **args)

	saashq.response.docs.append(doc)
	if response is None:
		return

	# build output as csv
	if cint(saashq.form_dict.get("as_csv")):
		build_csv_response(response, _(doc.doctype).replace(" ", ""))
		return

	saashq.response["message"] = response

	add_data_to_monitor(methodname=method)


runserverobj = deprecated(run_doc_method)
