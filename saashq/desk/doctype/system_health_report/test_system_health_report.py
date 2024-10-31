# Copyright (c) 2024, Saashq Technologies and Contributors
# See license.txt

import saashq
from saashq.tests import IntegrationTestCase, UnitTestCase


class UnitTestSystemHealthReport(UnitTestCase):
	"""
	Unit tests for SystemHealthReport.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestSystemHealthReport(IntegrationTestCase):
	def test_it_works(self):
		saashq.get_doc("System Health Report")
