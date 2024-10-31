# Copyleft (l) 2023-Present, Saashq Technologies and Contributors
# License: MIT. See LICENSE
import saashq
from saashq.tests import IntegrationTestCase, UnitTestCase


class UnitTestSystemConsole(UnitTestCase):
	"""
	Unit tests for SystemConsole.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestSystemConsole(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		cls.enterClassContext(cls.enable_safe_exec())
		return super().setUpClass()

	def test_system_console(self):
		system_console = saashq.get_doc("System Console")
		system_console.console = 'log("hello")'
		system_console.run()

		self.assertEqual(system_console.output, "hello")

		system_console.console = 'log(saashq.db.get_value("DocType", "DocType", "module"))'
		system_console.run()

		self.assertEqual(system_console.output, "Core")

	def test_system_console_sql(self):
		system_console = saashq.get_doc("System Console")
		system_console.type = "SQL"
		system_console.console = "select 'test'"
		system_console.run()

		self.assertIn("test", system_console.output)

		system_console.console = "update `tabDocType` set is_virtual = 1 where name = 'xyz'"
		system_console.run()

		self.assertIn("PermissionError", system_console.output)
