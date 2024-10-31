# Copyright (c) 2019, Saashq Technologies and Contributors
# License: MIT. See LICENSE
import saashq
from saashq.core.doctype.user.user import get_system_users
from saashq.desk.form.assign_to import add as assign_task
from saashq.tests import IntegrationTestCase, UnitTestCase


class UnitTestNotificationLog(UnitTestCase):
	"""
	Unit tests for NotificationLog.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestNotificationLog(IntegrationTestCase):
	def test_assignment(self):
		todo = get_todo()
		user = get_user()

		assign_task(
			{"assign_to": [user], "doctype": "ToDo", "name": todo.name, "description": todo.description}
		)
		log_type = saashq.db.get_value(
			"Notification Log", {"document_type": "ToDo", "document_name": todo.name}, "type"
		)
		self.assertEqual(log_type, "Assignment")

	def test_share(self):
		todo = get_todo()
		user = get_user()

		saashq.share.add("ToDo", todo.name, user, notify=1)
		log_type = saashq.db.get_value(
			"Notification Log", {"document_type": "ToDo", "document_name": todo.name}, "type"
		)
		self.assertEqual(log_type, "Share")

		email = get_last_email_queue()
		content = f"Subject: {saashq.utils.get_fullname(saashq.session.user)} shared a document ToDo"
		self.assertTrue(content in email.message)


def get_last_email_queue():
	res = saashq.get_all("Email Queue", fields=["message"], order_by="creation desc", limit=1)
	return res[0]


def get_todo():
	if not saashq.get_all("ToDo"):
		return saashq.get_doc({"doctype": "ToDo", "description": "Test for Notification"}).insert()

	res = saashq.get_all("ToDo", limit=1)
	return saashq.get_cached_doc("ToDo", res[0].name)


def get_user():
	return get_system_users(limit=1)[0]
