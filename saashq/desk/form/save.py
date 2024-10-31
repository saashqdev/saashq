# Copyright (c) 2015, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import json

import saashq
from saashq.core.doctype.submission_queue.submission_queue import queue_submission
from saashq.desk.form.load import run_onload
from saashq.model.docstatus import DocStatus
from saashq.monitor import add_data_to_monitor
from saashq.utils.scheduler import is_scheduler_inactive
from saashq.utils.telemetry import capture_doc


@saashq.whitelist()
def savedocs(doc, action):
	"""save / submit / update doclist"""
	doc = saashq.get_doc(json.loads(doc))
	capture_doc(doc, action)
	if doc.get("__islocal") and doc.name.startswith("new-" + doc.doctype.lower().replace(" ", "-")):
		# required to relink missing attachments if they exist.
		doc.__temporary_name = doc.name
	set_local_name(doc)

	# action
	doc.docstatus = {
		"Save": DocStatus.draft(),
		"Submit": DocStatus.submitted(),
		"Update": DocStatus.submitted(),
		"Cancel": DocStatus.cancelled(),
	}[action]

	if doc.docstatus.is_submitted():
		if action == "Submit" and doc.meta.queue_in_background and not is_scheduler_inactive():
			queue_submission(doc, action)
			return
		doc.submit()
	else:
		doc.save()

	# update recent documents
	run_onload(doc)
	send_updated_docs(doc)

	add_data_to_monitor(doctype=doc.doctype, action=action)
	saashq.msgprint(saashq._("Saved"), indicator="green", alert=True)


@saashq.whitelist()
def cancel(doctype=None, name=None, workflow_state_fieldname=None, workflow_state=None):
	"""cancel a doclist"""
	doc = saashq.get_doc(doctype, name)
	capture_doc(doc, "Cancel")

	if workflow_state_fieldname and workflow_state:
		doc.set(workflow_state_fieldname, workflow_state)
	doc.cancel()
	send_updated_docs(doc)
	saashq.msgprint(saashq._("Cancelled"), indicator="red", alert=True)


@saashq.whitelist()
def discard(doctype: str, name: str | int):
	"""discard a draft document"""
	doc = saashq.get_doc(doctype, name)
	capture_doc(doc, "Discard")

	doc.discard()
	send_updated_docs(doc)
	saashq.msgprint(saashq._("Discarded"), indicator="red", alert=True)


def send_updated_docs(doc):
	from .load import get_docinfo

	get_docinfo(doc)

	d = doc.as_dict()
	if hasattr(doc, "localname"):
		d["localname"] = doc.localname

	saashq.response.docs.append(d)


def set_local_name(doc):
	def _set_local_name(d):
		if doc.get("__islocal") or d.get("__islocal"):
			d.localname = d.name
			d.name = None

	_set_local_name(doc)
	for child in doc.get_all_children():
		_set_local_name(child)

	if doc.get("__newname"):
		doc.name = doc.get("__newname")
