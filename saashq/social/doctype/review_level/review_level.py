# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

# import saashq
from saashq.model.document import Document


class ReviewLevel(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		level_name: DF.Data
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		review_points: DF.Int
		role: DF.Link
	# end: auto-generated types

	pass
