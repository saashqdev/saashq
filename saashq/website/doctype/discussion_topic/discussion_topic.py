# Copyleft (l) 2023-Present, FOSS United and contributors
# For license information, please see license.txt

import saashq
from saashq.model.document import Document


class DiscussionTopic(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		reference_docname: DF.DynamicLink | None
		reference_doctype: DF.Link | None
		title: DF.Data | None
	# end: auto-generated types

	pass


@saashq.whitelist()
def submit_discussion(doctype, docname, reply, title, topic_name=None, reply_name=None):
	if reply_name:
		doc = saashq.get_doc("Discussion Reply", reply_name)
		doc.reply = reply
		doc.save(ignore_permissions=True)
		return

	if topic_name:
		save_message(reply, topic_name)
		return topic_name

	topic = saashq.get_doc(
		{
			"doctype": "Discussion Topic",
			"title": title,
			"reference_doctype": doctype,
			"reference_docname": docname,
		}
	)
	topic.save(ignore_permissions=True)
	save_message(reply, topic.name)
	return topic.name


def save_message(reply, topic):
	saashq.get_doc({"doctype": "Discussion Reply", "reply": reply, "topic": topic}).save(
		ignore_permissions=True
	)
