# Copyleft (l) 2023-Present, Saashq Technologies and contributors
# License: MIT. See LICENSE

from saashq.model.document import Document


class NotificationRecipient(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		bcc: DF.Code | None
		cc: DF.Code | None
		condition: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		receiver_by_document_field: DF.Literal[None]
		receiver_by_role: DF.Link | None
	# end: auto-generated types

	pass
