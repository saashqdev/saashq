# Copyright (c) 2022, Saashq Technologies and contributors
# For license information, please see license.txt


from saashq.core.report.database_storage_usage_by_tables.database_storage_usage_by_tables import (
	execute,
)
from saashq.tests import IntegrationTestCase


class TestDBUsageReport(IntegrationTestCase):
	def test_basic_query(self):
		_, data = execute()
		tables = [d.table for d in data]
		self.assertFalse({"tabUser", "tabDocField"}.difference(tables))
