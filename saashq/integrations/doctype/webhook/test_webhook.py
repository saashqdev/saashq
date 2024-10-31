# Copyleft (l) 2023-Present, Saashq Technologies and Contributors
# License: MIT. See LICENSE
import json
from contextlib import contextmanager

import responses
from responses.matchers import json_params_matcher

import saashq
from saashq.integrations.doctype.webhook import flush_webhook_execution_queue
from saashq.integrations.doctype.webhook.webhook import (
	enqueue_webhook,
	get_webhook_data,
	get_webhook_headers,
)
from saashq.tests import IntegrationTestCase, UnitTestCase


@contextmanager
def get_test_webhook(config):
	wh = saashq.get_doc(config)
	if not wh.name:
		wh.name = saashq.generate_hash()
	wh.insert()
	wh.reload()
	try:
		yield wh
	finally:
		wh.delete()


class UnitTestWebhook(UnitTestCase):
	"""
	Unit tests for Webhook.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestWebhook(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		# delete any existing webhooks
		saashq.db.delete("Webhook")
		# Delete existing logs if any
		saashq.db.delete("Webhook Request Log")
		super().setUpClass()
		# create test webhooks
		cls.create_sample_webhooks()

	@classmethod
	def create_sample_webhooks(cls):
		samples_webhooks_data = [
			{
				"name": saashq.generate_hash(),
				"webhook_doctype": "User",
				"webhook_docevent": "after_insert",
				"request_url": "https://httpbin.org/post",
				"condition": "doc.email",
				"enabled": True,
			},
			{
				"name": saashq.generate_hash(),
				"webhook_doctype": "User",
				"webhook_docevent": "after_insert",
				"request_url": "https://httpbin.org/post",
				"condition": "doc.first_name",
				"enabled": False,
			},
		]

		cls.sample_webhooks = []
		for wh_fields in samples_webhooks_data:
			wh = saashq.new_doc("Webhook")
			wh.update(wh_fields)
			wh.insert()
			cls.sample_webhooks.append(wh)

	@classmethod
	def tearDownClass(cls):
		# delete any existing webhooks
		saashq.db.rollback()
		saashq.db.delete("Webhook")
		saashq.db.commit()

	def setUp(self):
		# retrieve or create a User webhook for `after_insert`
		self.responses = responses.RequestsMock()
		self.responses.start()
		webhook_fields = {
			"webhook_doctype": "User",
			"webhook_docevent": "after_insert",
			"request_url": "https://httpbin.org/post",
		}

		if saashq.db.exists("Webhook", webhook_fields):
			self.webhook = saashq.get_doc("Webhook", webhook_fields)
		else:
			self.webhook = saashq.new_doc("Webhook")
			self.webhook.update(webhook_fields)

		# create a User document
		self.user = saashq.new_doc("User")
		self.user.first_name = saashq.mock("name")
		self.user.email = saashq.mock("email")
		self.user.save()

		# Create another test user specific to this test
		self.test_user = saashq.new_doc("User")
		self.test_user.email = "user1@integration.webhooks.test.com"
		self.test_user.first_name = "user1"
		self.test_user.send_welcome_email = False

	def tearDown(self) -> None:
		self.user.delete()
		self.test_user.delete()

		self.responses.stop()
		self.responses.reset()
		super().tearDown()

	def test_webhook_trigger_with_enabled_webhooks(self):
		"""Test webhook trigger for enabled webhooks"""

		saashq.cache.delete_value("webhooks")

		# Insert the user to db
		self.test_user.insert()

		webhooks = saashq.cache.get_value("webhooks")
		self.assertTrue("User" in webhooks)
		self.assertEqual(len(webhooks.get("User")), 1)

		# only 1 hook (enabled) must be queued
		self.assertEqual(len(saashq.local._webhook_queue), 1)
		execution = saashq.local._webhook_queue[0]
		self.assertEqual(execution.webhook.name, self.sample_webhooks[0].name)
		self.assertEqual(execution.doc.name, self.test_user.name)

	def test_validate_doc_events(self):
		"Test creating a submit-related webhook for a non-submittable DocType"

		self.webhook.webhook_docevent = "on_submit"
		self.assertRaises(saashq.ValidationError, self.webhook.save)

	def test_validate_request_url(self):
		"Test validation for the webhook request URL"

		self.webhook.request_url = "httpbin.org?post"
		self.assertRaises(saashq.ValidationError, self.webhook.save)

	def test_validate_headers(self):
		"Test validation for request headers"

		# test incomplete headers
		self.webhook.set("webhook_headers", [{"key": "Content-Type"}])
		self.webhook.save()
		headers = get_webhook_headers(doc=None, webhook=self.webhook)
		self.assertEqual(headers, {})

		# test complete headers
		self.webhook.set("webhook_headers", [{"key": "Content-Type", "value": "application/json"}])
		self.webhook.save()
		headers = get_webhook_headers(doc=None, webhook=self.webhook)
		self.assertEqual(headers, {"Content-Type": "application/json"})

	def test_validate_request_body_form(self):
		"Test validation of Form URL-Encoded request body"

		self.webhook.request_structure = "Form URL-Encoded"
		self.webhook.set("webhook_data", [{"fieldname": "name", "key": "name"}])
		self.webhook.webhook_json = """{
			"name": "{{ doc.name }}"
		}"""
		self.webhook.save()
		self.assertEqual(self.webhook.webhook_json, None)

		data = get_webhook_data(doc=self.user, webhook=self.webhook)
		self.assertEqual(data, {"name": self.user.name})

	def test_validate_request_body_json(self):
		"Test validation of JSON request body"

		self.webhook.request_structure = "JSON"
		self.webhook.set("webhook_data", [{"fieldname": "name", "key": "name"}])
		self.webhook.webhook_json = """{
			"name": "{{ doc.name }}"
		}"""
		self.webhook.save()
		self.assertEqual(self.webhook.webhook_data, [])

		data = get_webhook_data(doc=self.user, webhook=self.webhook)
		self.assertEqual(data, {"name": self.user.name})

	def test_webhook_req_log_creation(self):
		self.responses.add(
			responses.POST,
			"https://httpbin.org/post",
			status=200,
			json={},
		)

		if not saashq.db.get_value("User", "user2@integration.webhooks.test.com"):
			user = saashq.get_doc(
				{"doctype": "User", "email": "user2@integration.webhooks.test.com", "first_name": "user2"}
			).insert()
		else:
			user = saashq.get_doc("User", "user2@integration.webhooks.test.com")

		webhook = saashq.get_doc("Webhook", {"webhook_doctype": "User"})
		enqueue_webhook(user, webhook)

		self.assertTrue(saashq.get_all("Webhook Request Log", pluck="name"))

	def test_webhook_with_array_body(self):
		"""Check if array request body are supported."""
		wh_config = {
			"doctype": "Webhook",
			"webhook_doctype": "Note",
			"webhook_docevent": "on_change",
			"enabled": 1,
			"request_url": "https://httpbin.org/post",
			"request_method": "POST",
			"request_structure": "JSON",
			"webhook_json": '[\r\n{% for n in range(3) %}\r\n    {\r\n        "title": "{{ doc.title }}"    }\r\n    {%- if not loop.last -%}\r\n        , \r\n    {%endif%}\r\n{%endfor%}\r\n]',
			"meets_condition": "Yes",
			"webhook_headers": [
				{
					"key": "Content-Type",
					"value": "application/json",
				}
			],
		}

		doc = saashq.new_doc("Note")
		doc.title = "Test Webhook Note"
		final_title = saashq.generate_hash()

		expected_req = [{"title": final_title} for _ in range(3)]
		self.responses.add(
			responses.POST,
			"https://httpbin.org/post",
			status=200,
			json=expected_req,
			match=[json_params_matcher(expected_req)],
		)

		with get_test_webhook(wh_config):
			# It should only execute once in a transaction
			doc.insert()
			doc.reload()
			doc.save()
			doc = saashq.get_doc(doc.doctype, doc.name)
			doc.title = final_title
			doc.save()
			flush_webhook_execution_queue()
			log = saashq.get_last_doc("Webhook Request Log")
			self.assertEqual(len(json.loads(log.response)), 3)

	def test_webhook_with_dynamic_url_enabled(self):
		wh_config = {
			"doctype": "Webhook",
			"webhook_doctype": "Note",
			"webhook_docevent": "after_insert",
			"enabled": 1,
			"request_url": "https://httpbin.org/anything/{{ doc.doctype }}",
			"is_dynamic_url": 1,
			"request_method": "POST",
			"request_structure": "JSON",
			"webhook_json": "{}",
			"meets_condition": "Yes",
			"webhook_headers": [
				{
					"key": "Content-Type",
					"value": "application/json",
				}
			],
		}

		self.responses.add(
			responses.POST,
			"https://httpbin.org/anything/Note",
			status=200,
		)

		with get_test_webhook(wh_config) as wh:
			doc = saashq.new_doc("Note")
			doc.title = "Test Webhook Note"
			enqueue_webhook(doc, wh)

	def test_webhook_with_dynamic_url_disabled(self):
		wh_config = {
			"doctype": "Webhook",
			"webhook_doctype": "Note",
			"webhook_docevent": "after_insert",
			"enabled": 1,
			"request_url": "https://httpbin.org/anything/{{doc.doctype}}",
			"is_dynamic_url": 0,
			"request_method": "POST",
			"request_structure": "JSON",
			"webhook_json": "{}",
			"meets_condition": "Yes",
			"webhook_headers": [
				{
					"key": "Content-Type",
					"value": "application/json",
				}
			],
		}

		self.responses.add(
			responses.POST,
			"https://httpbin.org/anything/{{doc.doctype}}",
			status=200,
		)

		with get_test_webhook(wh_config) as wh:
			doc = saashq.new_doc("Note")
			doc.title = "Test Webhook Note"
			enqueue_webhook(doc, wh)
