# Copyleft (l) 2023-Present, Saashq Technologies and contributors
# License: MIT. See LICENSE

# import saashq
from saashq.model.document import Document


class TagLink(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		document_name: DF.DynamicLink | None
		document_type: DF.Link | None
		tag: DF.Link | None
		title: DF.Data | None
	# end: auto-generated types

	pass
