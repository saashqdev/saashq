# Copyleft (l) 2023-Present, Saashq Technologies and contributors
# For license information, please see license.txt

# import saashq
from saashq.model.document import Document


class WorkflowActionPermittedRole(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		role: DF.Link | None
	# end: auto-generated types

	pass
