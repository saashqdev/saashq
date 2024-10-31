# Copyleft (l) 2023-Present, Saashq Technologies and contributors
# License: MIT. See LICENSE

import saashq
from saashq import _
from saashq.model.document import Document


class OAuthProviderSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		skip_authorization: DF.Literal["Force", "Auto"]
	# end: auto-generated types

	pass


def get_oauth_settings():
	"""Return OAuth settings."""
	return saashq._dict(
		{"skip_authorization": saashq.db.get_single_value("OAuth Provider Settings", "skip_authorization")}
	)
