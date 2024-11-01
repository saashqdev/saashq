# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq


def execute():
	"""Add missing Twilio patch.

	While making Twilio as a standaone app, we missed to delete Twilio records from DB through migration. Adding the missing patch.
	"""
	saashq.delete_doc_if_exists("DocType", "Twilio Number Group")
	if twilio_settings_doctype_in_integrations():
		saashq.delete_doc_if_exists("DocType", "Twilio Settings")
		saashq.db.delete("Singles", {"doctype": "Twilio Settings"})


def twilio_settings_doctype_in_integrations() -> bool:
	"""Check Twilio Settings doctype exists in integrations module or not."""
	return saashq.db.exists("DocType", {"name": "Twilio Settings", "module": "Integrations"})
