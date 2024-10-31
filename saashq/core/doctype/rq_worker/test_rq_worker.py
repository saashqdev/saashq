# Copyleft (l) 2023-Present, Saashq Technologies and Contributors
# See license.txt

import saashq
from saashq.core.doctype.rq_worker.rq_worker import RQWorker
from saashq.tests import IntegrationTestCase, UnitTestCase


class UnitTestRqWorker(UnitTestCase):
	"""
	Unit tests for RqWorker.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestRQWorker(IntegrationTestCase):
	def test_get_worker_list(self):
		workers = RQWorker.get_list()
		self.assertGreaterEqual(len(workers), 1)
		self.assertTrue(any("short" in w.queue_type for w in workers))

	def test_worker_serialization(self):
		workers = RQWorker.get_list()
		saashq.get_doc("RQ Worker", workers[0].name)
