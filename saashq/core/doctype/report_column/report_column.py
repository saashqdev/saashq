# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

# import saashq
from saashq.model.document import Document


class ReportColumn(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		fieldname: DF.Data
		fieldtype: DF.Literal[
			"Check",
			"Currency",
			"Data",
			"Date",
			"Datetime",
			"Duration",
			"Dynamic Link",
			"Float",
			"Fold",
			"Int",
			"Link",
			"Select",
			"Time",
		]
		label: DF.Data
		options: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		width: DF.Int
	# end: auto-generated types

	pass
