# Copyleft (l) 2023-Present, Saashq Technologies and contributors
# License: MIT. See LICENSE

from saashq.model.document import Document


class ListFilter(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		filter_name: DF.Data | None
		filters: DF.LongText | None
		for_user: DF.Link | None
		reference_doctype: DF.Link | None
	# end: auto-generated types

	pass