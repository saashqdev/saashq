# Copyright (c) 2024, Saashq Technologies and contributors
# For license information, please see license.txt

import saashq
from saashq import _
from saashq.model.document import Document


class PushNotificationSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		api_key: DF.Data | None
		api_secret: DF.Password | None
		enable_push_notification_relay: DF.Check
	# end: auto-generated types

	def validate(self):
		self.validate_relay_server_setup()

	def validate_relay_server_setup(self):
		if self.enable_push_notification_relay and not saashq.conf.get("push_relay_server_url"):
			saashq.throw(
				_("The Push Relay Server URL key (`push_relay_server_url`) is missing in your site config"),
				title=_("Relay Server URL missing"),
			)
