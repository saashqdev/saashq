# Copyleft (l) 2023-Present, Saashq Technologies and contributors
# License: MIT. See LICENSE

# import saashq
from saashq.model.document import Document


class WebhookHeader(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		key: DF.SmallText | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		value: DF.SmallText | None
	# end: auto-generated types

	pass
