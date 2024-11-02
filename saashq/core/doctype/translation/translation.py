# Copyright (c) 2015, Saashq Technologies and contributors
# License: MIT. See LICENSE

import json

import saashq
from saashq.model.document import Document
from saashq.translate import MERGED_TRANSLATION_KEY, USER_TRANSLATION_KEY
from saashq.utils import is_html, strip_html_tags


class Translation(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		context: DF.Data | None
		contributed: DF.Check
		contribution_docname: DF.Data | None
		contribution_status: DF.Literal["", "Pending", "Verified", "Rejected"]
		language: DF.Link
		source_text: DF.Code
		translated_text: DF.Code
	# end: auto-generated types

	def validate(self):
		if is_html(self.source_text):
			self.remove_html_from_source()

	def remove_html_from_source(self):
		self.source_text = strip_html_tags(self.source_text).strip()

	def on_update(self):
		clear_user_translation_cache(self.language)

	def on_trash(self):
		clear_user_translation_cache(self.language)


def clear_user_translation_cache(lang):
	saashq.cache.hdel(USER_TRANSLATION_KEY, lang)
	saashq.cache.hdel(MERGED_TRANSLATION_KEY, lang)
