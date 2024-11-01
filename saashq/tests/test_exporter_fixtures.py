# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE
import os

import saashq
import saashq.defaults
from saashq.core.doctype.data_import.data_import import export_csv
from saashq.tests import IntegrationTestCase


class TestDataImportFixtures(IntegrationTestCase):
	def setUp(self):
		pass

	# start test for Client Script
	def test_Custom_Script_fixture_simple(self):
		fixture = "Client Script"
		path = saashq.scrub(fixture) + "_original_style.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Custom_Script_fixture_simple_name_equal_default(self):
		fixture = ["Client Script", {"name": ["Item"]}]
		path = saashq.scrub(fixture[0]) + "_simple_name_equal_default.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Custom_Script_fixture_simple_name_equal(self):
		fixture = ["Client Script", {"name": ["Item"], "op": "="}]
		path = saashq.scrub(fixture[0]) + "_simple_name_equal.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Custom_Script_fixture_simple_name_not_equal(self):
		fixture = ["Client Script", {"name": ["Item"], "op": "!="}]
		path = saashq.scrub(fixture[0]) + "_simple_name_not_equal.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	# without [] around the name...
	def test_Custom_Script_fixture_simple_name_at_least_equal(self):
		fixture = ["Client Script", {"name": "Item-Cli"}]
		path = saashq.scrub(fixture[0]) + "_simple_name_at_least_equal.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Custom_Script_fixture_multi_name_equal(self):
		fixture = ["Client Script", {"name": ["Item", "Customer"], "op": "="}]
		path = saashq.scrub(fixture[0]) + "_multi_name_equal.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Custom_Script_fixture_multi_name_not_equal(self):
		fixture = ["Client Script", {"name": ["Item", "Customer"], "op": "!="}]
		path = saashq.scrub(fixture[0]) + "_multi_name_not_equal.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Custom_Script_fixture_empty_object(self):
		fixture = ["Client Script", {}]
		path = saashq.scrub(fixture[0]) + "_empty_object_should_be_all.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Custom_Script_fixture_just_list(self):
		fixture = ["Client Script"]
		path = saashq.scrub(fixture[0]) + "_just_list_should_be_all.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	# Client Script regular expression
	def test_Custom_Script_fixture_rex_no_flags(self):
		fixture = ["Client Script", {"name": r"^[i|A]"}]
		path = saashq.scrub(fixture[0]) + "_rex_no_flags.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Custom_Script_fixture_rex_with_flags(self):
		fixture = ["Client Script", {"name": r"^[i|A]", "flags": "L,M"}]
		path = saashq.scrub(fixture[0]) + "_rex_with_flags.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	# start test for Custom Field
	def test_Custom_Field_fixture_simple(self):
		fixture = "Custom Field"
		path = saashq.scrub(fixture) + "_original_style.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Custom_Field_fixture_simple_name_equal_default(self):
		fixture = ["Custom Field", {"name": ["Item-vat"]}]
		path = saashq.scrub(fixture[0]) + "_simple_name_equal_default.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Custom_Field_fixture_simple_name_equal(self):
		fixture = ["Custom Field", {"name": ["Item-vat"], "op": "="}]
		path = saashq.scrub(fixture[0]) + "_simple_name_equal.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Custom_Field_fixture_simple_name_not_equal(self):
		fixture = ["Custom Field", {"name": ["Item-vat"], "op": "!="}]
		path = saashq.scrub(fixture[0]) + "_simple_name_not_equal.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	# without [] around the name...
	def test_Custom_Field_fixture_simple_name_at_least_equal(self):
		fixture = ["Custom Field", {"name": "Item-va"}]
		path = saashq.scrub(fixture[0]) + "_simple_name_at_least_equal.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Custom_Field_fixture_multi_name_equal(self):
		fixture = ["Custom Field", {"name": ["Item-vat", "Bin-vat"], "op": "="}]
		path = saashq.scrub(fixture[0]) + "_multi_name_equal.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Custom_Field_fixture_multi_name_not_equal(self):
		fixture = ["Custom Field", {"name": ["Item-vat", "Bin-vat"], "op": "!="}]
		path = saashq.scrub(fixture[0]) + "_multi_name_not_equal.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Custom_Field_fixture_empty_object(self):
		fixture = ["Custom Field", {}]
		path = saashq.scrub(fixture[0]) + "_empty_object_should_be_all.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Custom_Field_fixture_just_list(self):
		fixture = ["Custom Field"]
		path = saashq.scrub(fixture[0]) + "_just_list_should_be_all.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	# Custom Field regular expression
	def test_Custom_Field_fixture_rex_no_flags(self):
		fixture = ["Custom Field", {"name": r"^[r|L]"}]
		path = saashq.scrub(fixture[0]) + "_rex_no_flags.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Custom_Field_fixture_rex_with_flags(self):
		fixture = ["Custom Field", {"name": r"^[i|A]", "flags": "L,M"}]
		path = saashq.scrub(fixture[0]) + "_rex_with_flags.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	# start test for Doctype
	def test_Doctype_fixture_simple(self):
		fixture = "ToDo"
		path = "Doctype_" + saashq.scrub(fixture) + "_original_style_should_be_all.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Doctype_fixture_simple_name_equal_default(self):
		fixture = ["ToDo", {"name": ["TDI00000008"]}]
		path = "Doctype_" + saashq.scrub(fixture[0]) + "_simple_name_equal_default.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Doctype_fixture_simple_name_equal(self):
		fixture = ["ToDo", {"name": ["TDI00000002"], "op": "="}]
		path = "Doctype_" + saashq.scrub(fixture[0]) + "_simple_name_equal.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Doctype_simple_name_not_equal(self):
		fixture = ["ToDo", {"name": ["TDI00000002"], "op": "!="}]
		path = "Doctype_" + saashq.scrub(fixture[0]) + "_simple_name_not_equal.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	# without [] around the name...
	def test_Doctype_fixture_simple_name_at_least_equal(self):
		fixture = ["ToDo", {"name": "TDI"}]
		path = "Doctype_" + saashq.scrub(fixture[0]) + "_simple_name_at_least_equal.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Doctype_multi_name_equal(self):
		fixture = ["ToDo", {"name": ["TDI00000002", "TDI00000008"], "op": "="}]
		path = "Doctype_" + saashq.scrub(fixture[0]) + "_multi_name_equal.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Doctype_multi_name_not_equal(self):
		fixture = ["ToDo", {"name": ["TDI00000002", "TDI00000008"], "op": "!="}]
		path = "Doctype_" + saashq.scrub(fixture[0]) + "_multi_name_not_equal.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Doctype_fixture_empty_object(self):
		fixture = ["ToDo", {}]
		path = "Doctype_" + saashq.scrub(fixture[0]) + "_empty_object_should_be_all.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Doctype_fixture_just_list(self):
		fixture = ["ToDo"]
		path = "Doctype_" + saashq.scrub(fixture[0]) + "_just_list_should_be_all.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	# Doctype regular expression
	def test_Doctype_fixture_rex_no_flags(self):
		fixture = ["ToDo", {"name": r"^TDi"}]
		path = "Doctype_" + saashq.scrub(fixture[0]) + "_rex_no_flags_should_be_all.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)

	def test_Doctype_fixture_rex_with_flags(self):
		fixture = ["ToDo", {"name": r"^TDi", "flags": "L,M"}]
		path = "Doctype_" + saashq.scrub(fixture[0]) + "_rex_with_flags_should_be_none.csv"

		export_csv(fixture, path)
		self.assertTrue(True)
		os.remove(path)
