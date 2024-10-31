# Copyright (c) 2020, Saashq Technologies and Contributors
# License: MIT. See LICENSE
import saashq
from saashq.tests import IntegrationTestCase, UnitTestCase


class UnitTestWorkspace(UnitTestCase):
	"""
	Unit tests for Workspace.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestWorkspace(IntegrationTestCase):
	def setUp(self):
		create_module("Test Module")

	def tearDown(self):
		saashq.db.delete("Workspace", {"module": "Test Module"})
		saashq.db.delete("DocType", {"module": "Test Module"})
		saashq.delete_doc("Module Def", "Test Module")

	# TODO: FIX ME - flaky test!!!
	# def test_workspace_with_cards_specific_to_a_country(self):
	# 	workspace = create_workspace()
	# 	insert_card(workspace, "Card Label 1", "DocType 1", "DocType 2", "France")
	# 	insert_card(workspace, "Card Label 2", "DocType A", "DocType B")

	# 	workspace.insert(ignore_if_duplicate = True)

	# 	cards = workspace.get_link_groups()

	# 	if saashq.get_system_settings('country') == "France":
	# 		self.assertEqual(len(cards), 2)
	# 	else:
	# 		self.assertEqual(len(cards), 1)


def create_module(module_name):
	module = saashq.get_doc({"doctype": "Module Def", "module_name": module_name, "app_name": "saashq"})
	module.insert(ignore_if_duplicate=True)

	return module


def create_workspace(**args):
	workspace = saashq.new_doc("Workspace")
	args = saashq._dict(args)

	workspace.name = args.name or "Test Workspace"
	workspace.label = args.label or "Test Workspace"
	workspace.category = args.category or "Modules"
	workspace.is_standard = args.is_standard or 1
	workspace.module = "Test Module"

	return workspace


def insert_card(workspace, card_label, doctype1, doctype2, country=None):
	workspace.append("links", {"type": "Card Break", "label": card_label, "only_for": country})

	create_doctype(doctype1, "Test Module")
	workspace.append(
		"links",
		{
			"type": "Link",
			"label": doctype1,
			"only_for": country,
			"link_type": "DocType",
			"link_to": doctype1,
		},
	)

	create_doctype(doctype2, "Test Module")
	workspace.append(
		"links",
		{
			"type": "Link",
			"label": doctype2,
			"only_for": country,
			"link_type": "DocType",
			"link_to": doctype2,
		},
	)


def create_doctype(doctype_name, module):
	saashq.get_doc(
		{
			"doctype": "DocType",
			"name": doctype_name,
			"module": module,
			"custom": 1,
			"autoname": "field:title",
			"fields": [
				{"label": "Title", "fieldname": "title", "reqd": 1, "fieldtype": "Data"},
				{"label": "Description", "fieldname": "description", "fieldtype": "Small Text"},
				{"label": "Date", "fieldname": "date", "fieldtype": "Date"},
				{"label": "Duration", "fieldname": "duration", "fieldtype": "Duration"},
				{"label": "Number", "fieldname": "number", "fieldtype": "Int"},
				{"label": "Number", "fieldname": "another_number", "fieldtype": "Int"},
			],
			"permissions": [{"role": "System Manager"}],
		}
	).insert(ignore_if_duplicate=True)
