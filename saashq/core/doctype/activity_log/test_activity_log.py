# Copyright (c) 2015, Saashq Technologies and Contributors
# License: MIT. See LICENSE
import time

import saashq
from saashq.auth import CookieManager, LoginManager
from saashq.tests import IntegrationTestCase, UnitTestCase


class UnitTestActivityLog(UnitTestCase):
	"""
	Unit tests for ActivityLog.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestActivityLog(IntegrationTestCase):
	def setUp(self) -> None:
		saashq.set_user("Administrator")

	def test_activity_log(self):
		# test user login log
		saashq.local.form_dict = saashq._dict(
			{
				"cmd": "login",
				"sid": "Guest",
				"pwd": self.ADMIN_PASSWORD or "admin",
				"usr": "Administrator",
			}
		)

		saashq.local.request_ip = "127.0.0.1"
		saashq.local.cookie_manager = CookieManager()
		saashq.local.login_manager = LoginManager()

		auth_log = self.get_auth_log()
		self.assertFalse(saashq.form_dict.pwd)
		self.assertEqual(auth_log.status, "Success")

		# test user logout log
		saashq.local.login_manager.logout()
		auth_log = self.get_auth_log(operation="Logout")
		self.assertEqual(auth_log.status, "Success")

		# test invalid login
		saashq.form_dict.update({"pwd": "password"})
		self.assertRaises(saashq.AuthenticationError, LoginManager)
		auth_log = self.get_auth_log()
		self.assertEqual(auth_log.status, "Failed")

		saashq.local.form_dict = saashq._dict()

	def get_auth_log(self, operation="Login"):
		names = saashq.get_all(
			"Activity Log",
			filters={
				"user": "Administrator",
				"operation": operation,
			},
			order_by="`creation` DESC",
		)

		name = names[0]
		return saashq.get_doc("Activity Log", name)

	def test_brute_security(self):
		update_system_settings({"allow_consecutive_login_attempts": 3, "allow_login_after_fail": 5})

		saashq.local.form_dict = saashq._dict(
			{"cmd": "login", "sid": "Guest", "pwd": self.ADMIN_PASSWORD, "usr": "Administrator"}
		)

		saashq.local.request_ip = "127.0.0.1"
		saashq.local.cookie_manager = CookieManager()
		saashq.local.login_manager = LoginManager()

		auth_log = self.get_auth_log()
		self.assertEqual(auth_log.status, "Success")

		# test user logout log
		saashq.local.login_manager.logout()
		auth_log = self.get_auth_log(operation="Logout")
		self.assertEqual(auth_log.status, "Success")

		# test invalid login
		saashq.form_dict.update({"pwd": "password"})
		self.assertRaises(saashq.AuthenticationError, LoginManager)
		self.assertRaises(saashq.AuthenticationError, LoginManager)
		self.assertRaises(saashq.AuthenticationError, LoginManager)

		# REMOVE ME: current logic allows allow_consecutive_login_attempts+1 attempts
		# before raising security exception, remove below line when that is fixed.
		self.assertRaises(saashq.AuthenticationError, LoginManager)
		self.assertRaises(saashq.SecurityException, LoginManager)
		time.sleep(5)
		self.assertRaises(saashq.AuthenticationError, LoginManager)

		saashq.local.form_dict = saashq._dict()


def update_system_settings(args):
	doc = saashq.get_doc("System Settings")
	doc.update(args)
	doc.flags.ignore_mandatory = 1
	doc.save()
