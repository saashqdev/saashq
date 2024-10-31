import types

import saashq
from saashq.tests import IntegrationTestCase
from saashq.utils.safe_exec import ServerScriptNotEnabled, get_safe_globals, safe_exec


class TestSafeExec(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		cls.enterClassContext(cls.enable_safe_exec())
		return super().setUpClass()

	def test_import_fails(self):
		self.assertRaises(ImportError, safe_exec, "import os")

	def test_internal_attributes(self):
		self.assertRaises(SyntaxError, safe_exec, "().__class__.__call__")

	def test_utils(self):
		_locals = dict(out=None)
		safe_exec("""out = saashq.utils.cint("1")""", None, _locals)
		self.assertEqual(_locals["out"], 1)

	def test_safe_eval(self):
		TEST_CASES = {
			"1+1": 2,
			'"abc" in "abl"': False,
			'"a" in "abl"': True,
			'"a" in ("a", "b")': True,
			'"a" in {"a", "b"}': True,
			'"a" in {"a": 1, "b": 2}': True,
			'"a" in ["a" ,"b"]': True,
		}

		for code, result in TEST_CASES.items():
			self.assertEqual(saashq.safe_eval(code), result)

		self.assertRaises(AttributeError, saashq.safe_eval, "saashq.utils.os.path", get_safe_globals())

		# Doc/dict objects
		user = saashq.new_doc("User")
		user.user_type = "System User"
		user.enabled = 1
		self.assertTrue(saashq.safe_eval("user_type == 'System User'", eval_locals=user.as_dict()))
		self.assertEqual(
			"System User Test", saashq.safe_eval("user_type + ' Test'", eval_locals=user.as_dict())
		)
		self.assertEqual(1, saashq.safe_eval("int(enabled)", eval_locals=user.as_dict()))

	def test_safe_eval_wal(self):
		self.assertRaises(SyntaxError, saashq.safe_eval, "(x := (40+2))")

	def test_sql(self):
		_locals = dict(out=None)
		safe_exec(
			"""out = saashq.db.sql("select name from tabDocType where name='DocType'")""", None, _locals
		)
		self.assertEqual(_locals["out"][0][0], "DocType")

		self.assertRaises(
			saashq.PermissionError, safe_exec, 'saashq.db.sql("update tabToDo set description=NULL")'
		)

	def test_query_builder(self):
		_locals = dict(out=None)
		safe_exec(
			script="""out = saashq.qb.from_("User").select(saashq.qb.terms.PseudoColumn("Max(name)")).run()""",
			_globals=None,
			_locals=_locals,
		)
		self.assertEqual(saashq.db.sql("SELECT Max(name) FROM tabUser"), _locals["out"])

	def test_safe_query_builder(self):
		self.assertRaises(saashq.PermissionError, safe_exec, """saashq.qb.from_("User").delete().run()""")

	def test_call(self):
		# call non whitelisted method
		self.assertRaises(saashq.PermissionError, safe_exec, """saashq.call("saashq.get_user")""")

		# call whitelisted method
		safe_exec("""saashq.call("ping")""")

	def test_enqueue(self):
		# enqueue non whitelisted method
		self.assertRaises(
			saashq.PermissionError, safe_exec, """saashq.enqueue("saashq.get_user", now=True)"""
		)

		# enqueue whitelisted method
		safe_exec("""saashq.enqueue("ping", now=True)""")

	def test_ensure_getattrable_globals(self):
		def check_safe(objects):
			for obj in objects:
				if isinstance(obj, types.ModuleType | types.CodeType | types.TracebackType | types.FrameType):
					self.fail(f"{obj} wont work in safe exec.")
				elif isinstance(obj, dict):
					check_safe(obj.values())

		check_safe(get_safe_globals().values())

	def test_unsafe_objects(self):
		unsafe_global = {"saashq": saashq}
		self.assertRaises(SyntaxError, safe_exec, """saashq.msgprint("Hello")""", unsafe_global)

	def test_attrdict(self):
		# jinja
		saashq.render_template("{% set my_dict = _dict() %} {{- my_dict.works -}}")

		# RestrictedPython
		safe_exec("my_dict = _dict()")

	def test_write_wrapper(self):
		# Allow modifying _dict instance
		safe_exec("_dict().x = 1")

		# dont Allow modifying _dict class
		self.assertRaises(Exception, safe_exec, "_dict.x = 1")

	def test_print(self):
		test_str = saashq.generate_hash()
		safe_exec(f"print('{test_str}')")
		self.assertEqual(saashq.local.debug_log[-1], test_str)


class TestNoSafeExec(IntegrationTestCase):
	def test_safe_exec_disabled_by_default(self):
		self.assertRaises(ServerScriptNotEnabled, safe_exec, "pass")
