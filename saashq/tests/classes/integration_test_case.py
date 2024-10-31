import copy
import logging
from contextlib import AbstractContextManager, contextmanager
from types import MappingProxyType

import saashq
from saashq.utils import cint

from ..utils.generators import get_missing_records_module_overrides, make_test_records
from .unit_test_case import UnitTestCase

logger = logging.Logger(__file__)


class IntegrationTestCase(UnitTestCase):
	"""Integration test class for Saashq tests.

	Key features:
	- Automatic database setup and teardown
	- Utilities for managing database connections
	- Context managers for query counting and Redis call monitoring
	- Lazy loading of test record dependencies

	Note: If you override `setUpClass`, make sure to call `super().setUpClass()`
	to maintain the functionality of this base class.
	"""

	TEST_SITE = "test_site"

	SHOW_TRANSACTION_COMMIT_WARNINGS = False
	maxDiff = 10_000  # prints long diffs but useful in CI

	@classmethod
	def setUpClass(cls) -> None:
		if getattr(cls, "_integration_test_case_class_setup_done", None):
			return
		super().setUpClass()

		# Site initialization
		cls.TEST_SITE = getattr(saashq.local, "site", None) or cls.TEST_SITE
		saashq.init(cls.TEST_SITE)
		cls.ADMIN_PASSWORD = saashq.get_conf(cls.TEST_SITE).admin_password

		cls._primary_connection = saashq.local.db
		cls._secondary_connection = None

		# Create test record dependencies
		cls._newly_created_test_records = []
		if cls.doctype and cls.doctype not in saashq.local.test_objects:
			cls._newly_created_test_records += make_test_records(cls.doctype)
		elif not cls.doctype:
			to_add, ignore = get_missing_records_module_overrides(cls.module)
			if ignore:
				raise NotImplementedError(
					f"IGNORE_TEST_RECORD_DEPENDENCIES is only implement for test modules within a doctype folder {cls.module} {cls.doctype}"
				)
			for doctype in to_add:
				cls._newly_created_test_records += make_test_records(doctype)
		# flush changes done so far to avoid flake
		saashq.db.commit()
		cls.globalTestRecords = MappingProxyType(saashq.local.test_objects)
		if cls.SHOW_TRANSACTION_COMMIT_WARNINGS:
			saashq.db.before_commit.add(_commit_watcher)

		# enqueue teardown actions (executed in LIFO order)
		cls.addClassCleanup(_restore_thread_locals, copy.deepcopy(saashq.local.flags))
		cls.addClassCleanup(_rollback_db)
		cls._integration_test_case_class_setup_done = True

	@classmethod
	def tearDownClass(cls) -> None:
		# Add any necessary teardown code here
		super().tearDownClass()

	def setUp(self) -> None:
		super().setUp()
		# Add any per-test setup code here

	def tearDown(self) -> None:
		# Add any per-test teardown code here
		super().tearDown()

	@contextmanager
	def primary_connection(self) -> AbstractContextManager[None]:
		"""Switch to primary DB connection

		This is used for simulating multiple users performing actions by simulating two DB connections"""
		try:
			current_conn = saashq.local.db
			saashq.local.db = self._primary_connection
			yield
		finally:
			saashq.local.db = current_conn

	@contextmanager
	def secondary_connection(self) -> AbstractContextManager[None]:
		"""Switch to secondary DB connection."""
		if self._secondary_connection is None:
			saashq.connect()  # get second connection
			self._secondary_connection = saashq.local.db

		try:
			current_conn = saashq.local.db
			saashq.local.db = self._secondary_connection
			yield
		finally:
			saashq.local.db = current_conn
			self.addCleanup(self._rollback_connections)

	def _rollback_connections(self) -> None:
		self._primary_connection.rollback()
		self._secondary_connection.rollback()

	@contextmanager
	def assertQueryCount(self, count: int) -> AbstractContextManager[None]:
		queries = []

		def _sql_with_count(*args, **kwargs):
			ret = orig_sql(*args, **kwargs)
			queries.append(args[0].last_query)
			return ret

		try:
			orig_sql = saashq.db.__class__.sql
			saashq.db.__class__.sql = _sql_with_count
			yield
			self.assertLessEqual(len(queries), count, msg="Queries executed: \n" + "\n\n".join(queries))
		finally:
			saashq.db.__class__.sql = orig_sql

	@contextmanager
	def assertRedisCallCounts(self, count: int) -> AbstractContextManager[None]:
		commands = []

		def execute_command_and_count(*args, **kwargs):
			ret = orig_execute(*args, **kwargs)
			key_len = 2
			if "H" in args[0]:
				key_len = 3
			commands.append((args)[:key_len])
			return ret

		try:
			orig_execute = saashq.cache.execute_command
			saashq.cache.execute_command = execute_command_and_count
			yield
			self.assertLessEqual(
				len(commands), count, msg="commands executed: \n" + "\n".join(str(c) for c in commands)
			)
		finally:
			saashq.cache.execute_command = orig_execute

	@contextmanager
	def assertRowsRead(self, count: int) -> AbstractContextManager[None]:
		rows_read = 0

		def _sql_with_count(*args, **kwargs):
			nonlocal rows_read

			ret = orig_sql(*args, **kwargs)
			# count of last touched rows as per DB-API 2.0 https://peps.python.org/pep-0249/#rowcount
			rows_read += cint(saashq.db._cursor.rowcount)
			return ret

		try:
			orig_sql = saashq.db.sql
			saashq.db.sql = _sql_with_count
			yield
			self.assertLessEqual(rows_read, count, msg="Queries read more rows than expected")
		finally:
			saashq.db.sql = orig_sql


def _commit_watcher():
	import traceback

	logger.warning("Transaction committed during tests.")
	traceback.print_stack(limit=10)


def _rollback_db():
	saashq.db.value_cache = {}
	saashq.db.rollback()


def _restore_thread_locals(flags):
	saashq.local.flags = flags
	saashq.local.error_log = []
	saashq.local.message_log = []
	saashq.local.debug_log = []
	saashq.local.conf = saashq._dict(saashq.get_site_config())
	saashq.local.cache = {}
	saashq.local.lang = "en"
	saashq.local.preload_assets = {"style": [], "script": [], "icons": []}

	if hasattr(saashq.local, "request"):
		delattr(saashq.local, "request")
