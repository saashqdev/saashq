# Copyright (c) 2015, Saashq Technologies and contributors
# License: MIT. See LICENSE

import saashq
from saashq.model.document import Document


class EmailQueueRecipient(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		error: DF.Code | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		recipient: DF.Data | None
		status: DF.Literal["", "Not Sent", "Sent"]
	# end: auto-generated types

	DOCTYPE = "Email Queue Recipient"

	def is_mail_to_be_sent(self):
		return self.status == "Not Sent"

	def is_mail_sent(self):
		return self.status == "Sent"

	def update_db(self, commit=False, **kwargs):
		saashq.db.set_value(self.DOCTYPE, self.name, kwargs)
		if commit:
			saashq.db.commit()


def on_doctype_update():
	"""Index required for log clearing, modified is not indexed on child table by default"""
	saashq.db.add_index("Email Queue Recipient", ["modified"])
