# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE
import json

import saashq
from saashq.tests import IntegrationTestCase, UnitTestCase
from saashq.utils import set_request
from saashq.website.doctype.web_form.web_form import accept
from saashq.website.serve import get_response_content

EXTRA_TEST_RECORD_DEPENDENCIES = ["Web Form"]


class UnitTestWebForm(UnitTestCase):
	"""
	Unit tests for WebForm.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestWebForm(IntegrationTestCase):
	def setUp(self):
		saashq.conf.disable_website_cache = True

	def tearDown(self):
		saashq.conf.disable_website_cache = False

	def test_accept(self):
		saashq.set_user("Administrator")

		doc = {
			"doctype": "Event",
			"subject": "_Test Event Web Form",
			"description": "_Test Event Description",
			"starts_on": "2014-09-09",
		}

		accept(web_form="manage-events", data=json.dumps(doc))

		self.event_name = saashq.db.get_value("Event", {"subject": "_Test Event Web Form"})
		self.assertTrue(self.event_name)

	def test_edit(self):
		self.test_accept()

		doc = {
			"doctype": "Event",
			"subject": "_Test Event Web Form",
			"description": "_Test Event Description 1",
			"starts_on": "2014-09-09",
			"name": self.event_name,
		}

		self.assertNotEqual(
			saashq.db.get_value("Event", self.event_name, "description"), doc.get("description")
		)

		accept("manage-events", json.dumps(doc))

		self.assertEqual(saashq.db.get_value("Event", self.event_name, "description"), doc.get("description"))

	def test_webform_render(self):
		set_request(method="GET", path="manage-events/new")
		content = get_response_content("manage-events/new")
		self.assertIn('<h1 class="ellipsis">New Manage Events</h1>', content)
		self.assertIn('data-doctype="Web Form"', content)
		self.assertIn('data-path="manage-events/new"', content)
		self.assertIn('source-type="Generator"', content)

	def test_webform_html_meta_is_added(self):
		set_request(method="GET", path="manage-events/new")
		content = self.normalize_html(get_response_content("manage-events/new"))

		self.assertIn(self.normalize_html('<meta name="title" content="Test Meta Form Title">'), content)
		self.assertIn(
			self.normalize_html('<meta property="og:title" content="Test Meta Form Title">'), content
		)
		self.assertIn(
			self.normalize_html('<meta property="og:description" content="Test Meta Form Description">'),
			content,
		)
		self.assertIn(
			self.normalize_html('<meta property="og:image" content="https://saashq.org/files/saashq.png">'),
			content,
		)
