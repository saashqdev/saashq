# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import json

import saashq
from saashq import _
from saashq.desk.doctype.bulk_update.bulk_update import show_progress
from saashq.model.document import Document
from saashq.model.workflow import get_workflow_name


class DeletedDocument(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		data: DF.Code | None
		deleted_doctype: DF.Data | None
		deleted_name: DF.Data | None
		new_name: DF.ReadOnly | None
		restored: DF.Check
	# end: auto-generated types

	no_feed_on_delete = True

	@staticmethod
	def clear_old_logs(days=180):
		from saashq.query_builder import Interval
		from saashq.query_builder.functions import Now

		table = saashq.qb.DocType("Deleted Document")
		saashq.db.delete(table, filters=(table.creation < (Now() - Interval(days=days))))


@saashq.whitelist()
def restore(name, alert=True):
	deleted = saashq.get_doc("Deleted Document", name)

	if deleted.restored:
		saashq.throw(_("Document {0} Already Restored").format(name), exc=saashq.DocumentAlreadyRestored)

	doc = saashq.get_doc(json.loads(deleted.data))

	try:
		doc.insert()
	except saashq.DocstatusTransitionError:
		saashq.msgprint(_("Cancelled Document restored as Draft"))
		doc.docstatus = 0
		active_workflow = get_workflow_name(doc.doctype)
		if active_workflow:
			workflow_state_fieldname = saashq.get_value("Workflow", active_workflow, "workflow_state_field")
			if doc.get(workflow_state_fieldname):
				doc.set(workflow_state_fieldname, None)
		doc.insert()

	doc.add_comment("Edit", _("restored {0} as {1}").format(deleted.deleted_name, doc.name))

	deleted.new_name = doc.name
	deleted.restored = 1
	deleted.db_update()

	if alert:
		saashq.msgprint(_("Document Restored"))


@saashq.whitelist()
def bulk_restore(docnames):
	docnames = saashq.parse_json(docnames)
	message = _("Restoring Deleted Document")
	restored, invalid, failed = [], [], []

	for i, d in enumerate(docnames):
		try:
			show_progress(docnames, message, i + 1, d)
			restore(d, alert=False)
			saashq.db.commit()
			restored.append(d)

		except saashq.DocumentAlreadyRestored:
			saashq.clear_last_message()
			invalid.append(d)

		except Exception:
			saashq.clear_last_message()
			failed.append(d)
			saashq.db.rollback()

	return {"restored": restored, "invalid": invalid, "failed": failed}
