# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

# License: MIT. See LICENSE

import saashq
from saashq.model.document import Document


class BlogSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		allow_guest_to_comment: DF.Check
		blog_introduction: DF.SmallText | None
		blog_title: DF.Data | None
		browse_by_category: DF.Check
		comment_limit: DF.Int
		cta_label: DF.Data | None
		cta_url: DF.Data | None
		enable_social_sharing: DF.Check
		like_limit: DF.Int
		preview_image: DF.AttachImage | None
		show_cta_in_blog: DF.Check
		subtitle: DF.Data | None
		title: DF.Data | None
	# end: auto-generated types

	def on_update(self):
		from saashq.website.utils import clear_cache

		clear_cache("blog")
		clear_cache("writers")


def get_like_limit():
	return saashq.db.get_single_value("Blog Settings", "like_limit") or 5


def get_comment_limit():
	return saashq.db.get_single_value("Blog Settings", "comment_limit") or 5
