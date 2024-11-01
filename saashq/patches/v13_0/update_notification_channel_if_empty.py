# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq


def execute():
	saashq.reload_doc("Email", "doctype", "Notification")

	notifications = saashq.get_all("Notification", {"is_standard": 1}, {"name", "channel"})
	for notification in notifications:
		if not notification.channel:
			saashq.db.set_value("Notification", notification.name, "channel", "Email", update_modified=False)
			saashq.db.commit()
