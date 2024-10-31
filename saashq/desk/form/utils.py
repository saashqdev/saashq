# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import json
from typing import TYPE_CHECKING

import saashq
import saashq.desk.form.load
import saashq.desk.form.meta
from saashq import _
from saashq.core.doctype.file.utils import extract_images_from_html
from saashq.desk.form.document_follow import follow_document

if TYPE_CHECKING:
	from saashq.core.doctype.comment.comment import Comment


@saashq.whitelist(methods=["DELETE", "POST"])
def remove_attach():
	"""remove attachment"""
	fid = saashq.form_dict.get("fid")
	saashq.delete_doc("File", fid)


@saashq.whitelist(methods=["POST", "PUT"])
def add_comment(
	reference_doctype: str, reference_name: str, content: str, comment_email: str, comment_by: str
) -> "Comment":
	"""Allow logged user with permission to read document to add a comment"""
	reference_doc = saashq.get_doc(reference_doctype, reference_name)
	reference_doc.check_permission()

	comment = saashq.new_doc("Comment")
	comment.update(
		{
			"comment_type": "Comment",
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"comment_email": comment_email,
			"comment_by": comment_by,
			"content": extract_images_from_html(reference_doc, content, is_private=True),
		}
	)
	comment.insert(ignore_permissions=True)

	if saashq.get_cached_value("User", saashq.session.user, "follow_commented_documents"):
		follow_document(comment.reference_doctype, comment.reference_name, saashq.session.user)

	return comment


@saashq.whitelist()
def update_comment(name, content):
	"""allow only owner to update comment"""
	doc = saashq.get_doc("Comment", name)

	if saashq.session.user not in ["Administrator", doc.owner]:
		saashq.throw(_("Comment can only be edited by the owner"), saashq.PermissionError)

	if doc.reference_doctype and doc.reference_name:
		reference_doc = saashq.get_doc(doc.reference_doctype, doc.reference_name)
		reference_doc.check_permission()

		doc.content = extract_images_from_html(reference_doc, content, is_private=True)
	else:
		doc.content = content

	doc.save(ignore_permissions=True)


@saashq.whitelist()
def get_next(doctype, value, prev, filters=None, sort_order="desc", sort_field="creation"):
	prev = int(prev)
	if not filters:
		filters = []
	if isinstance(filters, str):
		filters = json.loads(filters)

	# # condition based on sort order
	condition = ">" if sort_order.lower() == "asc" else "<"

	# switch the condition
	if prev:
		sort_order = "asc" if sort_order.lower() == "desc" else "desc"
		condition = "<" if condition == ">" else ">"

	# # add condition for next or prev item
	filters.append([doctype, sort_field, condition, saashq.get_value(doctype, value, sort_field)])

	res = saashq.get_list(
		doctype,
		fields=["name"],
		filters=filters,
		order_by=f"`tab{doctype}`.{sort_field}" + " " + sort_order,
		limit_start=0,
		limit_page_length=1,
		as_list=True,
	)

	if not res:
		saashq.msgprint(_("No further records"))
		return None
	else:
		return res[0][0]


def get_pdf_link(doctype, docname, print_format="Standard", no_letterhead=0):
	return f"/api/method/saashq.utils.print_format.download_pdf?doctype={doctype}&name={docname}&format={print_format}&no_letterhead={no_letterhead}"
