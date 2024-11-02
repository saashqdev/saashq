# Copyright (c) 2021, Saashq Technologies and contributors
# License: MIT. See LICENSE
from tenacity import retry, retry_if_exception_type, stop_after_attempt

import saashq
from saashq.model.document import Document
from saashq.utils import cstr


class AccessLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		columns: DF.HTMLEditor | None
		export_from: DF.Data | None
		file_type: DF.Data | None
		filters: DF.Code | None
		method: DF.Data | None
		page: DF.HTMLEditor | None
		reference_document: DF.Data | None
		report_name: DF.Data | None
		timestamp: DF.Datetime | None
		user: DF.Link | None
	# end: auto-generated types

	@staticmethod
	def clear_old_logs(days=30):
		from saashq.query_builder import Interval
		from saashq.query_builder.functions import Now

		table = saashq.qb.DocType("Access Log")
		saashq.db.delete(table, filters=(table.creation < (Now() - Interval(days=days))))


@saashq.whitelist()
def make_access_log(
	doctype=None,
	document=None,
	method=None,
	file_type=None,
	report_name=None,
	filters=None,
	page=None,
	columns=None,
):
	_make_access_log(
		doctype,
		document,
		method,
		file_type,
		report_name,
		filters,
		page,
		columns,
	)


@saashq.write_only()
@retry(
	stop=stop_after_attempt(3),
	retry=retry_if_exception_type(saashq.DuplicateEntryError),
	reraise=True,
)
def _make_access_log(
	doctype=None,
	document=None,
	method=None,
	file_type=None,
	report_name=None,
	filters=None,
	page=None,
	columns=None,
):
	user = saashq.session.user
	in_request = saashq.request and saashq.request.method == "GET"

	access_log = saashq.get_doc(
		{
			"doctype": "Access Log",
			"user": user,
			"export_from": doctype,
			"reference_document": document,
			"file_type": file_type,
			"report_name": report_name,
			"page": page,
			"method": method,
			"filters": cstr(filters) or None,
			"columns": columns,
		}
	)

	if saashq.flags.read_only:
		access_log.deferred_insert()
		return
	else:
		access_log.db_insert()

	# `saashq.db.commit` added because insert doesnt `commit` when called in GET requests like `printview`
	# dont commit in test mode. It must be tempting to put this block along with the in_request in the
	# whitelisted method...yeah, don't do it. That part would be executed possibly on a read only DB conn
	if not saashq.flags.in_test or in_request:
		saashq.db.commit()
