# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

# import saashq
from saashq.model.document import Document


class DashboardChartField(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		color: DF.Color | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		y_field: DF.Literal[None]
	# end: auto-generated types

	pass
