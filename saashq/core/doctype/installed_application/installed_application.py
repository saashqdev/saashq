# Copyright (c) 2020, Saashq Technologies and contributors
# License: MIT. See LICENSE

# import saashq
from saashq.model.document import Document


class InstalledApplication(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		app_name: DF.Data
		app_version: DF.Data
		git_branch: DF.Data
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
	# end: auto-generated types

	pass
