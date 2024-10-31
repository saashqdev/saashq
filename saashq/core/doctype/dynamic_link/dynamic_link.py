# Copyright (c) 2015, Saashq Technologies and contributors
# License: MIT. See LICENSE

import saashq
from saashq.model.document import Document


class DynamicLink(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		link_doctype: DF.Link
		link_name: DF.DynamicLink
		link_title: DF.ReadOnly | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
	# end: auto-generated types

	pass


def on_doctype_update():
	saashq.db.add_index("Dynamic Link", ["link_doctype", "link_name"])


def deduplicate_dynamic_links(doc):
	links, duplicate = [], False
	for l in doc.links or []:
		t = (l.link_doctype, l.link_name)
		if t not in links:
			links.append(t)
		else:
			duplicate = True

	if duplicate:
		doc.links = []
		for l in links:
			doc.append("links", dict(link_doctype=l[0], link_name=l[1]))
