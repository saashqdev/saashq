# Copyright (c) 2022, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import datetime
import decimal
import json
import mimetypes
import os
import sys
import uuid
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote

import werkzeug.utils
from werkzeug.exceptions import Forbidden, NotFound
from werkzeug.local import LocalProxy
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file

import saashq
import saashq.model.document
import saashq.sessions
import saashq.utils
from saashq import _
from saashq.core.doctype.access_log.access_log import make_access_log
from saashq.utils import format_timedelta

if TYPE_CHECKING:
	from saashq.core.doctype.file.file import File


def report_error(status_code):
	"""Build error. Show traceback in developer mode"""
	from saashq.api import ApiVersion, get_api_version

	allow_traceback = (
		(saashq.get_system_settings("allow_error_traceback") if saashq.db else False)
		and not saashq.local.flags.disable_traceback
		and (status_code != 404 or saashq.conf.logging)
	)

	traceback = saashq.utils.get_traceback()
	exc_type, exc_value, _ = sys.exc_info()

	match get_api_version():
		case ApiVersion.V1:
			if allow_traceback:
				saashq.errprint(traceback)
				saashq.response.exception = traceback.splitlines()[-1]
			saashq.response["exc_type"] = exc_type.__name__
		case ApiVersion.V2:
			error_log = {"type": exc_type.__name__}
			if allow_traceback:
				error_log["exception"] = traceback
			_link_error_with_message_log(error_log, exc_value, saashq.message_log)
			saashq.local.response.errors = [error_log]

	response = build_response("json")
	response.status_code = status_code

	return response


def _link_error_with_message_log(error_log, exception, message_logs):
	for message in list(message_logs):
		if message.get("__saashq_exc_id") == getattr(exception, "__saashq_exc_id", None):
			error_log.update(message)
			message_logs.remove(message)
			error_log.pop("raise_exception", None)
			error_log.pop("__saashq_exc_id", None)
			return


def build_response(response_type=None):
	if "docs" in saashq.local.response and not saashq.local.response.docs:
		del saashq.local.response["docs"]

	response_type_map = {
		"csv": as_csv,
		"txt": as_txt,
		"download": as_raw,
		"json": as_json,
		"pdf": as_pdf,
		"page": as_page,
		"redirect": redirect,
		"binary": as_binary,
	}

	return response_type_map[saashq.response.get("type") or response_type]()


def as_csv():
	response = Response()
	response.mimetype = "text/csv"
	filename = f"{saashq.response['doctype']}.csv"
	filename = filename.encode("utf-8").decode("unicode-escape", "ignore")
	response.headers.add("Content-Disposition", "attachment", filename=filename)
	response.data = saashq.response["result"]
	return response


def as_txt():
	response = Response()
	response.mimetype = "text"
	filename = f"{saashq.response['doctype']}.txt"
	filename = filename.encode("utf-8").decode("unicode-escape", "ignore")
	response.headers.add("Content-Disposition", "attachment", filename=filename)
	response.data = saashq.response["result"]
	return response


def as_raw():
	response = Response()
	response.mimetype = (
		saashq.response.get("content_type")
		or mimetypes.guess_type(saashq.response["filename"])[0]
		or "application/unknown"
	)
	filename = saashq.response["filename"].encode("utf-8").decode("unicode-escape", "ignore")
	response.headers.add(
		"Content-Disposition",
		saashq.response.get("display_content_as", "attachment"),
		filename=filename,
	)
	response.data = saashq.response["filecontent"]
	return response


def as_json():
	make_logs()

	response = Response()
	if saashq.local.response.http_status_code:
		response.status_code = saashq.local.response["http_status_code"]
		del saashq.local.response["http_status_code"]

	response.mimetype = "application/json"
	response.data = json.dumps(saashq.local.response, default=json_handler, separators=(",", ":"))
	return response


def as_pdf():
	response = Response()
	response.mimetype = "application/pdf"
	filename = saashq.response["filename"].encode("utf-8").decode("unicode-escape", "ignore")
	response.headers.add("Content-Disposition", None, filename=filename)
	response.data = saashq.response["filecontent"]
	return response


def as_binary():
	response = Response()
	response.mimetype = "application/octet-stream"
	filename = saashq.response["filename"]
	filename = filename.encode("utf-8").decode("unicode-escape", "ignore")
	response.headers.add("Content-Disposition", None, filename=filename)
	response.data = saashq.response["filecontent"]
	return response


def make_logs():
	"""make strings for msgprint and errprint"""

	from saashq.api import ApiVersion, get_api_version

	match get_api_version():
		case ApiVersion.V1:
			_make_logs_v1()
		case ApiVersion.V2:
			_make_logs_v2()


def _make_logs_v1():
	from saashq.utils.error import guess_exception_source

	response = saashq.local.response
	allow_traceback = saashq.get_system_settings("allow_error_traceback") if saashq.db else False

	if saashq.error_log and allow_traceback:
		if source := guess_exception_source(saashq.local.error_log and saashq.local.error_log[0]["exc"]):
			response["_exc_source"] = source
		response["exc"] = json.dumps([saashq.utils.cstr(d["exc"]) for d in saashq.local.error_log])

	if saashq.local.message_log:
		response["_server_messages"] = json.dumps([json.dumps(d) for d in saashq.local.message_log])

	if saashq.debug_log:
		response["_debug_messages"] = json.dumps(saashq.local.debug_log)

	if saashq.flags.error_message:
		response["_error_message"] = saashq.flags.error_message


def _make_logs_v2():
	response = saashq.local.response

	if saashq.local.message_log:
		response["messages"] = saashq.local.message_log

	if saashq.debug_log:
		response["debug"] = [{"message": m} for m in saashq.local.debug_log]


def json_handler(obj):
	"""serialize non-serializable data for json"""
	from collections.abc import Iterable
	from re import Match

	if isinstance(obj, datetime.date | datetime.datetime | datetime.time):
		return str(obj)

	elif isinstance(obj, datetime.timedelta):
		return format_timedelta(obj)

	elif isinstance(obj, decimal.Decimal):
		return float(obj)

	elif isinstance(obj, LocalProxy):
		return str(obj)

	elif isinstance(obj, Iterable):
		return list(obj)

	elif isinstance(obj, Match):
		return obj.string

	elif type(obj) == type or isinstance(obj, Exception):
		return repr(obj)

	elif callable(obj):
		return repr(obj)

	elif isinstance(obj, uuid.UUID):
		return str(obj)

	elif isinstance(obj, Path):
		return str(obj)

	elif hasattr(obj, "__json__"):
		return obj.__json__()

	elif hasattr(obj, "__value__"):  # order imporant: defer to __json__ if implemented
		return obj.__value__()

	else:
		raise TypeError(f"""Object of type {type(obj)} with value of {obj!r} is not JSON serializable""")


def as_page():
	"""print web page"""
	from saashq.website.serve import get_response

	return get_response(saashq.response["route"], http_status_code=saashq.response.get("http_status_code"))


def redirect():
	return werkzeug.utils.redirect(saashq.response.location)


def download_backup(path):
	try:
		saashq.only_for(("System Manager", "Administrator"))
		make_access_log(report_name="Backup")
	except saashq.PermissionError:
		raise Forbidden(
			_("You need to be logged in and have System Manager Role to be able to access backups.")
		)

	return send_private_file(path)


def download_private_file(path: str) -> Response:
	"""Checks permissions and sends back private file"""
	from saashq.core.doctype.file.utils import find_file_by_url

	if saashq.session.user == "Guest":
		raise Forbidden(_("You don't have permission to access this file"))

	file = find_file_by_url(path, name=saashq.form_dict.fid)
	if not file:
		raise Forbidden(_("You don't have permission to access this file"))

	make_access_log(doctype="File", document=file.name, file_type=os.path.splitext(path)[-1][1:])
	return send_private_file(path.split("/private", 1)[1])


def send_private_file(path: str) -> Response:
	path = os.path.join(saashq.local.conf.get("private_path", "private"), path.strip("/"))
	filename = os.path.basename(path)

	if saashq.local.request.headers.get("X-Use-X-Accel-Redirect"):
		path = "/protected/" + path
		response = Response()
		response.headers["X-Accel-Redirect"] = quote(saashq.utils.encode(path))

	else:
		filepath = saashq.utils.get_site_path(path)
		try:
			f = open(filepath, "rb")
		except OSError:
			raise NotFound

		response = Response(wrap_file(saashq.local.request.environ, f), direct_passthrough=True)

	# no need for content disposition and force download. let browser handle its opening.
	# Except for those that can be injected with scripts.

	extension = os.path.splitext(path)[1]
	blacklist = [".svg", ".html", ".htm", ".xml"]

	if extension.lower() in blacklist:
		response.headers.add("Content-Disposition", "attachment", filename=filename)

	response.mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"

	return response


def handle_session_stopped():
	from saashq.website.serve import get_response

	saashq.respond_as_web_page(
		_("Updating"),
		_("The system is being updated. Please refresh again after a few moments."),
		http_status_code=503,
		indicator_color="orange",
		fullpage=True,
		primary_action=None,
	)
	return get_response("message", http_status_code=503)
