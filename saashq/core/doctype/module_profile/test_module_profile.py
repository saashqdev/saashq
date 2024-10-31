# Copyright (c) 2020, Saashq Technologies and Contributors
# License: MIT. See LICENSE
import saashq
from saashq.tests import IntegrationTestCase, UnitTestCase


class UnitTestModuleProfile(UnitTestCase):
	"""
	Unit tests for ModuleProfile.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestModuleProfile(IntegrationTestCase):
	def test_make_new_module_profile(self):
		if not saashq.db.get_value("Module Profile", "_Test Module Profile"):
			saashq.get_doc(
				{
					"doctype": "Module Profile",
					"module_profile_name": "_Test Module Profile",
					"block_modules": [{"module": "Accounts"}],
				}
			).insert()

		# add to user and check
		if not saashq.db.get_value("User", "test-for-module_profile@example.com"):
			new_user = saashq.get_doc(
				{"doctype": "User", "email": "test-for-module_profile@example.com", "first_name": "Test User"}
			).insert()
		else:
			new_user = saashq.get_doc("User", "test-for-module_profile@example.com")

		new_user.module_profile = "_Test Module Profile"
		new_user.save()

		self.assertEqual(new_user.block_modules[0].module, "Accounts")
