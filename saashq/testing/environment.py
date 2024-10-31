"""
This module handles the setup and teardown of the test environment for Saashq applications.

Key components:
- _initialize_test_environment: Initializes the test environment for a given site
- _cleanup_after_tests: Performs cleanup operations after running tests
- _disable_scheduler_if_needed: Disables the scheduler if it's not already disabled
- IntegrationTestPreparation: A class to prepare the environment for integration tests

The module provides functionality for:
- Initializing the database connection
- Setting test-related flags
- Disabling the scheduler during tests
- Running 'before_tests' hooks
- Creating global test record dependencies

Usage:
These functions and classes are typically used by the test runner to set up
and tear down the test environment before and after test execution.
"""

import logging
import unittest

import saashq
import saashq.utils.scheduler
from saashq.tests.utils import make_test_records

from .runner import TestRunnerError
from .utils import debug_timer

logger = logging.getLogger(__name__)


@debug_timer
def _initialize_test_environment(site, config):
	"""Initialize the test environment"""
	logger.debug(f"Initializing test environment for site: {site}")
	saashq.init(site)
	if not saashq.db:
		saashq.connect()
	try:
		# require db access
		_disable_scheduler_if_needed()
		saashq.clear_cache()
	except Exception as e:
		logger.error(f"Error connecting to the database: {e!s}")
		raise TestRunnerError(f"Failed to connect to the database: {e}") from e

	# Set various test-related flags
	saashq.flags.in_test = True
	saashq.flags.print_messages = logger.getEffectiveLevel() < logging.INFO
	saashq.flags.tests_verbose = logger.getEffectiveLevel() < logging.INFO


def _cleanup_after_tests():
	"""Perform cleanup operations after running tests"""
	global scheduler_disabled_by_user
	if not scheduler_disabled_by_user:
		saashq.utils.scheduler.enable_scheduler()

	if saashq.db:
		# this commit ends the transaction
		saashq.db.commit()  # nosemgrep
		saashq.clear_cache()


# Global variable to track scheduler state
scheduler_disabled_by_user = False


def _disable_scheduler_if_needed():
	"""Disable scheduler if it's not already disabled"""
	global scheduler_disabled_by_user
	scheduler_disabled_by_user = saashq.utils.scheduler.is_scheduler_disabled(verbose=False)
	if not scheduler_disabled_by_user:
		saashq.utils.scheduler.disable_scheduler()


class IntegrationTestPreparation:
	def __init__(self, cfg):
		self.cfg = cfg

	def __call__(self, suite: unittest.TestSuite, app: str, category: str) -> None:
		"""Prepare the environment for integration tests."""
		if not self.cfg.skip_before_tests:
			self._run_before_test_hooks(app, category)
		else:
			logger.debug("Skipping before_tests hooks: Explicitly skipped")

		self._create_global_test_record_dependencies(app, category)

	@staticmethod
	@debug_timer
	def _run_before_test_hooks(app: str, category: str):
		"""Run 'before_tests' hooks"""
		logger.info(f'Running "before_tests" hooks for {category} tests on app: {app}')
		for hook_function in saashq.get_hooks("before_tests", app_name=app):
			logger.info(f'Running "before_tests" hook function {hook_function}')
			saashq.get_attr(hook_function)()

	@staticmethod
	@debug_timer
	def _create_global_test_record_dependencies(app: str, category: str):
		"""Create global test record dependencies"""
		test_module = saashq.get_module(f"{app}.tests")
		if hasattr(test_module, "global_test_dependencies"):
			logger.info(f"Creating global test record dependencies for {category} tests on {app} ...")
			for doctype in test_module.global_test_dependencies:
				logger.debug(f"Creating global test records for {doctype}")
				make_test_records(doctype, commit=True)
