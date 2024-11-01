# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

from saashq.model.document import Document


class WorkflowActionMaster(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		workflow_action_name: DF.Data
	# end: auto-generated types

	pass
