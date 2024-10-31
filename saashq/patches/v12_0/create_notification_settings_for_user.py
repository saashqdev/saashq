import saashq
from saashq.desk.doctype.notification_settings.notification_settings import (
	create_notification_settings,
)


def execute():
	saashq.reload_doc("desk", "doctype", "notification_settings")
	saashq.reload_doc("desk", "doctype", "notification_subscribed_document")

	users = saashq.get_all("User", fields=["name"])
	for user in users:
		create_notification_settings(user.name)
