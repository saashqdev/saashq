# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq
import saashq.monitor
from saashq.monitor import MONITOR_REDIS_KEY, get_trace_id
from saashq.tests import IntegrationTestCase
from saashq.utils import set_request
from saashq.utils.response import build_response


class TestMonitor(IntegrationTestCase):
	def setUp(self):
		saashq.conf.monitor = 1
		saashq.cache.delete_value(MONITOR_REDIS_KEY)

	def tearDown(self):
		saashq.conf.monitor = 0
		saashq.cache.delete_value(MONITOR_REDIS_KEY)

	def test_enable_monitor(self):
		set_request(method="GET", path="/api/method/saashq.ping")
		response = build_response("json")

		saashq.monitor.start()
		saashq.monitor.stop(response)

		logs = saashq.cache.lrange(MONITOR_REDIS_KEY, 0, -1)
		self.assertEqual(len(logs), 1)

		log = saashq.parse_json(logs[0].decode())
		self.assertTrue(log.duration)
		self.assertTrue(log.site)
		self.assertTrue(log.timestamp)
		self.assertTrue(log.uuid)
		self.assertTrue(log.request)
		self.assertEqual(log.transaction_type, "request")
		self.assertEqual(log.request["method"], "GET")

	def test_no_response(self):
		set_request(method="GET", path="/api/method/saashq.ping")

		saashq.monitor.start()
		saashq.monitor.stop(response=None)

		logs = saashq.cache.lrange(MONITOR_REDIS_KEY, 0, -1)
		self.assertEqual(len(logs), 1)

		log = saashq.parse_json(logs[0].decode())
		self.assertEqual(log.request["status_code"], 500)
		self.assertEqual(log.transaction_type, "request")
		self.assertEqual(log.request["method"], "GET")

	def test_job(self):
		saashq.utils.background_jobs.execute_job(
			saashq.local.site, "saashq.ping", None, None, {}, is_async=False
		)

		logs = saashq.cache.lrange(MONITOR_REDIS_KEY, 0, -1)
		self.assertEqual(len(logs), 1)
		log = saashq.parse_json(logs[0].decode())
		self.assertEqual(log.transaction_type, "job")
		self.assertTrue(log.job)
		self.assertEqual(log.job["method"], "saashq.ping")
		self.assertEqual(log.job["scheduled"], False)
		self.assertEqual(log.job["wait"], 0)

	def test_flush(self):
		set_request(method="GET", path="/api/method/saashq.ping")
		response = build_response("json")
		saashq.monitor.start()
		saashq.monitor.stop(response)

		open(saashq.monitor.log_file(), "w").close()
		saashq.monitor.flush()

		with open(saashq.monitor.log_file()) as f:
			logs = f.readlines()

		self.assertEqual(len(logs), 1)
		log = saashq.parse_json(logs[0])
		self.assertEqual(log.transaction_type, "request")

	def test_trace_ids(self):
		set_request(method="GET", path="/api/method/saashq.ping")
		response = build_response("json")
		saashq.monitor.start()
		saashq.db.sql("select 1")
		self.assertIn(get_trace_id(), str(saashq.db.last_query))
		saashq.monitor.stop(response)
