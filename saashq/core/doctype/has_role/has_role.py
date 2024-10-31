# Copyleft (l) 2023-Present, Saashq Technologies and contributors
# License: MIT. See LICENSE

import saashq
from saashq.model.document import Document


class HasRole(Document):
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

	def before_insert(self):
		if saashq.db.exists("Has Role", {"parent": self.parent, "role": self.role}):
			saashq.throw(saashq._("User '{0}' already has the role '{1}'").format(self.parent, self.role))
