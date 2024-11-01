# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq
from saashq.model.document import Document


class GoogleSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		api_key: DF.Data | None
		app_id: DF.Data | None
		client_id: DF.Data | None
		client_secret: DF.Password | None
		enable: DF.Check
		google_drive_picker_enabled: DF.Check
	# end: auto-generated types

	pass


@saashq.whitelist()
def get_file_picker_settings():
	"""Return all the data FileUploader needs to start the Google Drive Picker."""
	google_settings = saashq.get_single("Google Settings")
	if not (google_settings.enable and google_settings.google_drive_picker_enabled):
		return {}

	return {
		"enabled": True,
		"appId": google_settings.app_id,
		"clientId": google_settings.client_id,
	}
