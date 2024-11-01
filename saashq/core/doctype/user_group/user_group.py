# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq

# import saashq
from saashq.model.document import Document


class UserGroup(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.core.doctype.user_group_member.user_group_member import UserGroupMember
		from saashq.types import DF

		user_group_members: DF.TableMultiSelect[UserGroupMember]
	# end: auto-generated types

	def after_insert(self):
		saashq.cache.delete_key("user_groups")

	def on_trash(self):
		saashq.cache.delete_key("user_groups")
