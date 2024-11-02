# Copyright (c) 2021, Saashq Technologies and contributors
# License: MIT. See LICENSE

# import saashq
from saashq.model.document import Document


class PersonalDataDeletionStep(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		document_type: DF.Data
		fields: DF.SmallText | None
		filtered_by: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		partial: DF.Check
		status: DF.Literal["Pending", "Deleted"]
	# end: auto-generated types

	pass
