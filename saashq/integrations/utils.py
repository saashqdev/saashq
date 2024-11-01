# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import datetime
import json
from urllib.parse import parse_qs

import saashq
from saashq.utils import get_request_session


def make_request(method: str, url: str, auth=None, headers=None, data=None, json=None, params=None):
	auth = auth or ""
	data = data or {}
	headers = headers or {}

	try:
		s = get_request_session()
		response = saashq.flags.integration_request = s.request(
			method, url, data=data, auth=auth, headers=headers, json=json, params=params
		)
		response.raise_for_status()

		# Check whether the response has a content-type, before trying to check what it is
		if content_type := response.headers.get("content-type"):
			if content_type == "text/plain; charset=utf-8":
				return parse_qs(response.text)
			elif content_type.startswith("application/") and content_type.split(";")[0].endswith("json"):
				return response.json()
			elif response.text:
				return response.text
		return
	except Exception as exc:
		if saashq.flags.integration_request_doc:
			saashq.flags.integration_request_doc.log_error()
		else:
			saashq.log_error()
		raise exc


def make_get_request(url: str, **kwargs):
	"""Make a 'GET' HTTP request to the given `url` and return processed response.

	You can optionally pass the below parameters:

	* `headers`: Headers to be set in the request.
	* `params`: Query parameters to be passed in the request.
	* `auth`: Auth credentials.
	"""
	return make_request("GET", url, **kwargs)


def make_post_request(url: str, **kwargs):
	"""Make a 'POST' HTTP request to the given `url` and return processed response.

	You can optionally pass the below parameters:

	* `headers`: Headers to be set in the request.
	* `data`: Data to be passed in body of the request.
	* `json`: JSON to be passed in the request.
	* `params`: Query parameters to be passed in the request.
	* `auth`: Auth credentials.
	"""
	return make_request("POST", url, **kwargs)


def make_put_request(url: str, **kwargs):
	"""Make a 'PUT' HTTP request to the given `url` and return processed response.

	You can optionally pass the below parameters:

	* `headers`: Headers to be set in the request.
	* `data`: Data to be passed in body of the request.
	* `json`: JSON to be passed in the request.
	* `params`: Query parameters to be passed in the request.
	* `auth`: Auth credentials.
	"""
	return make_request("PUT", url, **kwargs)


def make_patch_request(url: str, **kwargs):
	"""Make a 'PATCH' HTTP request to the given `url` and return processed response.

	You can optionally pass the below parameters:

	* `headers`: Headers to be set in the request.
	* `data`: Data to be passed in body of the request.
	* `json`: JSON to be passed in the request.
	* `params`: Query parameters to be passed in the request.
	* `auth`: Auth credentials.
	"""
	return make_request("PATCH", url, **kwargs)


def make_delete_request(url: str, **kwargs):
	"""Make a 'DELETE' HTTP request to the given `url` and return processed response.

	You can optionally pass the below parameters:

	* `headers`: Headers to be set in the request.
	* `data`: Data to be passed in body of the request.
	* `json`: JSON to be passed in the request.
	* `params`: Query parameters to be passed in the request.
	* `auth`: Auth credentials.
	"""
	return make_request("DELETE", url, **kwargs)


def create_request_log(
	data,
	integration_type=None,
	service_name=None,
	name=None,
	error=None,
	request_headers=None,
	output=None,
	**kwargs,
):
	"""
	DEPRECATED: The parameter integration_type will be removed in the next major release.
	Use is_remote_request instead.
	"""
	if integration_type == "Remote":
		kwargs["is_remote_request"] = 1

	elif integration_type == "Subscription Notification":
		kwargs["request_description"] = integration_type

	reference_doctype = reference_docname = None
	if "reference_doctype" not in kwargs:
		if isinstance(data, str):
			data = json.loads(data)

		reference_doctype = data.get("reference_doctype")
		reference_docname = data.get("reference_docname")

	integration_request = saashq.get_doc(
		{
			"doctype": "Integration Request",
			"integration_request_service": service_name,
			"request_headers": get_json(request_headers),
			"data": get_json(data),
			"output": get_json(output),
			"error": get_json(error),
			"reference_doctype": reference_doctype,
			"reference_docname": reference_docname,
			**kwargs,
		}
	)

	if name:
		integration_request.flags._name = name

	integration_request.insert(ignore_permissions=True)
	saashq.db.commit()

	return integration_request


def get_json(obj):
	return obj if isinstance(obj, str) else saashq.as_json(obj, indent=1)


def json_handler(obj):
	if isinstance(obj, datetime.date | datetime.timedelta | datetime.datetime):
		return str(obj)
