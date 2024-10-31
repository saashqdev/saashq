# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE
import json

import saashq
from saashq.tests import IntegrationTestCase


class TestSeen(IntegrationTestCase):
	def tearDown(self):
		saashq.set_user("Administrator")

	def test_if_user_is_added(self):
		ev = saashq.get_doc(
			{
				"doctype": "Event",
				"subject": "test event for seen",
				"starts_on": "2016-01-01 10:10:00",
				"event_type": "Public",
			}
		).insert()

		saashq.set_user("test@example.com")

		from saashq.desk.form.load import getdoc

		# load the form
		getdoc("Event", ev.name)

		# reload the event
		ev = saashq.get_doc("Event", ev.name)

		self.assertTrue("test@example.com" in json.loads(ev._seen))

		# test another user
		saashq.set_user("test1@example.com")

		# load the form
		getdoc("Event", ev.name)

		# reload the event
		ev = saashq.get_doc("Event", ev.name)

		self.assertTrue("test@example.com" in json.loads(ev._seen))
		self.assertTrue("test1@example.com" in json.loads(ev._seen))

		ev.save()
		ev = saashq.get_doc("Event", ev.name)

		self.assertFalse("test@example.com" in json.loads(ev._seen))
		self.assertTrue("test1@example.com" in json.loads(ev._seen))
