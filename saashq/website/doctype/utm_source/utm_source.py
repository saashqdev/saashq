# Copyright (c) 2024, Saashq Technologies and contributors
# For license information, please see license.txt

import saashq
from saashq.model.document import Document


class UTMSource(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		description: DF.SmallText | None
		slug: DF.Data | None
	# end: auto-generated types

	def before_save(self):
		if self.slug:
			self.slug = saashq.utils.slug(self.slug)