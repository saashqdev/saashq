# Copyright (c) 2023, Saashq Technologies and Contributors
# See license.txt

import re

import saashq
import saashq.recorder
from saashq.core.doctype.recorder.recorder import _optimize_query, serialize_request
from saashq.query_builder.utils import db_type_is
from saashq.recorder import get as get_recorder_data
from saashq.tests import IntegrationTestCase, UnitTestCase
from saashq.tests.test_query_builder import run_only_if
from saashq.utils import set_request


class UnitTestRecorder(UnitTestCase):
	"""
	Unit tests for Recorder.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestRecorder(IntegrationTestCase):
	def setUp(self):
		self.start_recoder()

	def tearDown(self) -> None:
		saashq.recorder.stop()

	def start_recoder(self):
		saashq.recorder.stop()
		saashq.recorder.delete()
		set_request(path="/api/method/ping")
		saashq.recorder.start()
		saashq.recorder.record()

	def stop_recorder(self):
		saashq.recorder.dump()

	def test_recorder_list(self):
		saashq.get_all("User")  # trigger one query
		self.stop_recorder()
		requests = saashq.get_all("Recorder")
		self.assertGreaterEqual(len(requests), 1)
		request = saashq.get_doc("Recorder", requests[0].name)
		self.assertGreaterEqual(len(request.sql_queries), 1)
		queries = [sql_query.query for sql_query in request.sql_queries]
		match_flag = 0
		for query in queries:
			if bool(re.match("^[select.*from `tabUser`]", query, flags=re.IGNORECASE)):
				match_flag = 1
				break
		self.assertEqual(match_flag, 1)

	def test_recorder_list_filters(self):
		user = saashq.qb.DocType("User")
		saashq.qb.from_(user).select("name").run()
		self.stop_recorder()

		set_request(path="/api/method/abc")
		saashq.recorder.start()
		saashq.recorder.record()
		saashq.get_all("User")
		self.stop_recorder()

		requests = saashq.get_list(
			"Recorder", filters={"path": ("like", "/api/method/ping"), "number_of_queries": 1}
		)
		self.assertGreaterEqual(len(requests), 1)
		requests = saashq.get_list("Recorder", filters={"path": ("like", "/api/method/test")})
		self.assertEqual(len(requests), 0)

		requests = saashq.get_list("Recorder", filters={"method": "GET"})
		self.assertGreaterEqual(len(requests), 1)
		requests = saashq.get_list("Recorder", filters={"method": "POST"})
		self.assertEqual(len(requests), 0)

		requests = saashq.get_list("Recorder", order_by="path desc")
		self.assertEqual(requests[0].path, "/api/method/ping")

	def test_recorder_serialization(self):
		saashq.get_all("User")  # trigger one query
		self.stop_recorder()
		requests = saashq.get_all("Recorder")
		request_doc = get_recorder_data(requests[0].name)
		self.assertIsInstance(serialize_request(request_doc), dict)


class TestQueryOptimization(IntegrationTestCase):
	@run_only_if(db_type_is.MARIADB)
	def test_query_optimizer(self):
		suggested_index = _optimize_query(
			"""select name from
			`tabUser` u
			join `tabHas Role` r
			on r.parent = u.name
			where email='xyz'
			and creation > '2023'
			and bio like '%xyz%'
			"""
		)
		self.assertEqual(suggested_index.table, "tabUser")
		self.assertEqual(suggested_index.column, "email")
