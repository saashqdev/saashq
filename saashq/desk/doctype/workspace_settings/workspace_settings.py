# Copyright (c) 2024, Saashq Technologies and contributors
# For license information, please see license.txt

import json

import saashq
from saashq.model.document import Document


class WorkspaceSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		workspace_setup_completed: DF.Check
		workspace_visibility_json: DF.JSON
	# end: auto-generated types

	pass

	def on_update(self):
		saashq.clear_cache()


@saashq.whitelist()
def set_sequence(sidebar_items):
	if not WorkspaceSettings("Workspace Settings").has_permission():
		saashq.throw_permission_error()

	cnt = 1
	for item in json.loads(sidebar_items):
		saashq.db.set_value("Workspace", item.get("name"), "sequence_id", cnt)
		saashq.db.set_value("Workspace", item.get("name"), "parent_page", item.get("parent") or "")
		cnt += 1

	saashq.clear_cache()
	saashq.toast(saashq._("Updated"))
