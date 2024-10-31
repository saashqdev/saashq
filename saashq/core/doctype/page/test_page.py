# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE
import os
import unittest
from unittest.mock import patch

import saashq
from saashq.tests import IntegrationTestCase, UnitTestCase


class UnitTestPage(UnitTestCase):
	"""
	Unit tests for Page.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestPage(IntegrationTestCase):
	def test_naming(self):
		self.assertRaises(
			saashq.NameError,
			saashq.get_doc(doctype="Page", page_name="DocType", module="Core").insert,
		)

	@unittest.skipUnless(
		os.access(saashq.get_app_path("saashq"), os.W_OK), "Only run if saashq app paths is writable"
	)
	@patch.dict(saashq.conf, {"developer_mode": 1})
	def test_trashing(self):
		page = saashq.new_doc("Page", page_name=saashq.generate_hash(), module="Core").insert()

		page.delete()
		saashq.db.commit()

		module_path = saashq.get_module_path(page.module)
		dir_path = os.path.join(module_path, "page", saashq.scrub(page.name))

		self.assertFalse(os.path.exists(dir_path))
