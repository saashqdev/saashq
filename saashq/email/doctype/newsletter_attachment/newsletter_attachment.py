# Copyright (c) 2021, Saashq Technologies and contributors
# For license information, please see license.txt

# import saashq
from saashq.model.document import Document


class NewsletterAttachment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		attachment: DF.Attach
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
	# end: auto-generated types

	pass
