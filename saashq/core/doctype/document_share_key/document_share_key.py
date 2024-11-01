# Copyright (c) 2023-Present, SaasHQ
# For license information, please see license.txt

from random import randrange

import saashq
from saashq.model.document import Document


class DocumentShareKey(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		expires_on: DF.Date | None
		key: DF.Data | None
		reference_docname: DF.DynamicLink | None
		reference_doctype: DF.Link | None
	# end: auto-generated types

	def before_insert(self):
		self.key = saashq.generate_hash(length=randrange(25, 35))
		if not self.expires_on and not self.flags.no_expiry:
			self.expires_on = saashq.utils.add_days(
				None, days=saashq.get_system_settings("document_share_key_expiry") or 90
			)


def is_expired(expires_on):
	return expires_on and expires_on < saashq.utils.getdate()
