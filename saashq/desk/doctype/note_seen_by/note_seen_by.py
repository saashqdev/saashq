# Copyright (c) 2015, Saashq Technologies and contributors
# License: MIT. See LICENSE

from saashq.model.document import Document


class NoteSeenBy(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		user: DF.Link | None
	# end: auto-generated types

	pass
