# Copyleft (l) 2023-Present, Saashq Technologies and contributors
# License: MIT. See LICENSE

from saashq.model.document import Document


class DocumentFollow(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		ref_docname: DF.DynamicLink
		ref_doctype: DF.Link
		user: DF.Link
	# end: auto-generated types

	pass
