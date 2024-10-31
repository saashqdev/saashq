# Copyleft (l) 2023-Present, Saashq Technologies and contributors
# License: MIT. See LICENSE

from saashq.model.document import Document


class EmailFlagQueue(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		action: DF.Literal["Read", "Unread"]
		communication: DF.Data | None
		email_account: DF.Data | None
		is_completed: DF.Check
		uid: DF.Data | None
	# end: auto-generated types

	pass
