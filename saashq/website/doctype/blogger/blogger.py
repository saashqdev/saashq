# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

# License: MIT. See LICENSE

import saashq
from saashq import _
from saashq.model.document import Document


class Blogger(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		avatar: DF.AttachImage | None
		bio: DF.SmallText | None
		disabled: DF.Check
		full_name: DF.Data
		short_name: DF.Data
		user: DF.Link | None
	# end: auto-generated types

	def validate(self):
		if self.user and not saashq.db.exists("User", self.user):
			# for data import
			saashq.get_doc(
				{"doctype": "User", "email": self.user, "first_name": self.user.split("@", 1)[0]}
			).insert()

	def on_update(self):
		"if user is set, then update all older blogs"

		from saashq.website.doctype.blog_post.blog_post import clear_blog_cache

		clear_blog_cache()

		if self.user:
			for blog in saashq.db.sql_list(
				"""select name from `tabBlog Post` where owner=%s
				and ifnull(blogger,'')=''""",
				self.user,
			):
				b = saashq.get_doc("Blog Post", blog)
				b.blogger = self.name
				b.save()

			saashq.permissions.add_user_permission("Blogger", self.name, self.user)
