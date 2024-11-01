"""
Welcome to the Deprecation Dumpster: Where Old Code Goes to Party! 🎉🗑️

This file is the final resting place (or should we say, "retirement home"?) for all the deprecated functions and methods of the Saashq framework. It's like a code nursing home, but with more monkey-patching and less bingo.

Each function or method that checks in here comes with its own personalized decorator, complete with:
1. The date it was marked for deprecation (its "over the hill" birthday)
2. The Saashq version in which it will be removed (its "graduation" to the great codebase in the sky)
3. A user-facing note on alternative solutions (its "parting wisdom")

Warning: The global namespace herein is more patched up than a sailor's favorite pair of jeans. Proceed with caution and a sense of humor!

Remember, deprecated doesn't mean useless - it just means these functions are enjoying their golden years before their final bow. Treat them with respect, and maybe bring them some virtual prune juice.

Enjoy your stay in the Deprecation Dumpster, where every function gets a second chance to shine (or at least, to not break everything).
"""

import inspect
import os
import sys
import warnings


def colorize(text, color_code):
	if sys.stdout.isatty():
		return f"\033[{color_code}m{text}\033[0m"
	return text


class Color:
	RED = 91
	YELLOW = 93
	CYAN = 96


class SaashqDeprecationWarning(Warning):
	...


try:
	# since python 3.13, PEP 702
	from warnings import deprecated as _deprecated
except ImportError:
	import functools
	import warnings
	from collections.abc import Callable
	from typing import Optional, TypeVar, Union, overload

	T = TypeVar("T", bound=Callable)

	def _deprecated(message: str, category=SaashqDeprecationWarning, stacklevel=1) -> Callable[[T], T]:
		def decorator(func: T) -> T:
			@functools.wraps(func)
			def wrapper(*args, **kwargs):
				if message:
					warning_msg = f"{func.__name__} is deprecated.\n{message}"
				else:
					warning_msg = f"{func.__name__} is deprecated."
				warnings.warn(warning_msg, category=category, stacklevel=stacklevel + 1)
				return func(*args, **kwargs)

			return wrapper
			wrapper.__deprecated__ = True  # hint for the type checker

		return decorator


def deprecated(original: str, marked: str, graduation: str, msg: str, stacklevel: int = 1):
	"""Decorator to wrap a function/method as deprecated.

	Arguments:
	        - original: saashq.utils.make_esc  (fully qualified)
	        - marked: 2024-09-13  (the date it has been marked)
	        - graduation: v17  (generally: current version + 2)
	"""

	def decorator(func):
		# Get the filename of the caller
		frame = inspect.currentframe()
		caller_filepath = frame.f_back.f_code.co_filename
		if os.path.basename(caller_filepath) != "deprecation_dumpster.py":
			raise RuntimeError(
				colorize("The deprecated function ", Color.YELLOW)
				+ colorize(func.__name__, Color.CYAN)
				+ colorize(" can only be called from ", Color.YELLOW)
				+ colorize("saashq/deprecation_dumpster.py\n", Color.CYAN)
				+ colorize("Move the entire function there and import it back via adding\n ", Color.YELLOW)
				+ colorize(f"from saashq.deprecation_dumpster import {func.__name__}\n", Color.CYAN)
				+ colorize("to file\n ", Color.YELLOW)
				+ colorize(caller_filepath, Color.CYAN)
			)

		func.__name__ = original
		wrapper = _deprecated(
			colorize(f"It was marked on {marked} for removal from {graduation} with note: ", Color.RED)
			+ colorize(f"{msg}", Color.YELLOW),
			stacklevel=stacklevel,
		)

		return functools.update_wrapper(wrapper, func)(func)

	return decorator


def deprecation_warning(marked: str, graduation: str, msg: str):
	"""Warn in-place from a deprecated code path, for objects use `@deprecated` decorator from the deprectation_dumpster"

	Arguments:
	        - marked: 2024-09-13  (the date it has been marked)
	        - graduation: v17  (generally: current version + 2)
	"""

	warnings.warn(
		colorize(
			f"This codepath was marked (DATE: {marked}) deprecated"
			f" for removal (from {graduation} onwards); note:\n ",
			Color.RED,
		)
		+ colorize(f"{msg}\n", Color.YELLOW),
		category=DeprecationWarning,
		stacklevel=2,
	)


### Party starts here
def _old_deprecated(func):
	return deprecated(
		"saashq.deprecations.deprecated",
		"2024-09-13",
		"v17",
		"Make use of the saashq/deprecation_dumpster.py file, instead. 🎉🗑️",
	)(_deprecated("")(func))


def _old_deprecation_warning(msg):
	@deprecated(
		"saashq.deprecations.deprecation_warning",
		"2024-09-13",
		"v17",
		"Use saashq.deprecation_dumpster.deprecation_warning, instead. 🎉🗑️",
	)
	def deprecation_warning(message, category=DeprecationWarning, stacklevel=1):
		warnings.warn(message=message, category=category, stacklevel=stacklevel + 2)

	return deprecation_warning(msg)


@deprecated("saashq.utils.make_esc", "unknown", "v17", "Not used anymore.")
def make_esc(esc_chars):
	"""
	Function generator for Escaping special characters
	"""
	return lambda s: "".join("\\" + c if c in esc_chars else c for c in s)


@deprecated(
	"saashq.db.is_column_missing",
	"unknown",
	"v17",
	"Renamed to saashq.db.is_missing_column.",
)
def is_column_missing(e):
	import saashq

	return saashq.db.is_missing_column(e)


@deprecated(
	"saashq.desk.doctype.bulk_update.bulk_update",
	"unknown",
	"v17",
	"Unknown.",
)
def show_progress(docnames, message, i, description):
	import saashq

	n = len(docnames)
	saashq.publish_progress(float(i) * 100 / n, title=message, description=description)


@deprecated(
	"saashq.client.get_js",
	"unknown",
	"v17",
	"Unknown.",
)
def get_js(items):
	"""Load JS code files.  Will also append translations
	and extend `saashq._messages`

	:param items: JSON list of paths of the js files to be loaded."""
	import json

	import saashq
	from saashq import _

	items = json.loads(items)
	out = []
	for src in items:
		src = src.strip("/").split("/")

		if ".." in src or src[0] != "assets":
			saashq.throw(_("Invalid file path: {0}").format("/".join(src)))

		contentpath = os.path.join(saashq.local.sites_path, *src)
		with open(contentpath) as srcfile:
			code = saashq.utils.cstr(srcfile.read())

		out.append(code)

	return out


@deprecated(
	"saashq.utils.print_format.read_multi_pdf",
	"unknown",
	"v17",
	"Unknown.",
)
def read_multi_pdf(output) -> bytes:
	from io import BytesIO

	with BytesIO() as merged_pdf:
		output.write(merged_pdf)
		return merged_pdf.getvalue()


@deprecated("saashq.gzip_compress", "unknown", "v17", "Use py3 methods directly (this was compat for py2).")
def gzip_compress(data, compresslevel=9):
	"""Compress data in one shot and return the compressed string.
	Optional argument is the compression level, in range of 0-9.
	"""
	import io
	from gzip import GzipFile

	buf = io.BytesIO()
	with GzipFile(fileobj=buf, mode="wb", compresslevel=compresslevel) as f:
		f.write(data)
	return buf.getvalue()


@deprecated("saashq.gzip_decompress", "unknown", "v17", "Use py3 methods directly (this was compat for py2).")
def gzip_decompress(data):
	"""Decompress a gzip compressed string in one shot.
	Return the decompressed string.
	"""
	import io
	from gzip import GzipFile

	with GzipFile(fileobj=io.BytesIO(data)) as f:
		return f.read()


@deprecated(
	"saashq.email.doctype.email_queue.email_queue.send_mail",
	"unknown",
	"v17",
	"Unknown.",
)
def send_mail(email_queue_name, smtp_server_instance=None):
	"""This is equivalent to EmailQueue.send.

	This provides a way to make sending mail as a background job.
	"""
	from saashq.email.doctype.email_queue.email_queue import EmailQueue

	record = EmailQueue.find(email_queue_name)
	record.send(smtp_server_instance=smtp_server_instance)


@deprecated(
	"saashq.geo.country_info.get_translated_dict",
	"unknown",
	"v17",
	"Use saashq.geo.country_info.get_translated_countries, instead.",
)
def get_translated_dict():
	from saashq.geo.country_info import get_translated_countries

	return get_translated_countries()


@deprecated(
	"User.validate_roles",
	"unknown",
	"v17",
	"Use User.populate_role_profile_roles, instead.",
)
def validate_roles(self):
	self.populate_role_profile_roles()


@deprecated("saashq.tests_runner.get_modules", "2024-20-08", "v17", "use saashq.tests.utils.get_modules")
def test_runner_get_modules(doctype):
	from saashq.tests.utils import get_modules

	return get_modules(doctype)


@deprecated(
	"saashq.tests_runner.make_test_records", "2024-20-08", "v17", "use saashq.tests.utils.make_test_records"
)
def test_runner_make_test_records(*args, **kwargs):
	from saashq.tests.utils import make_test_records

	return make_test_records(*args, **kwargs)


@deprecated(
	"saashq.tests_runner.make_test_objects", "2024-20-08", "v17", "use saashq.tests.utils.make_test_objects"
)
def test_runner_make_test_objects(*args, **kwargs):
	from saashq.tests.utils import make_test_objects

	return make_test_objects(*args, **kwargs)


@deprecated(
	"saashq.tests_runner.make_test_records_for_doctype",
	"2024-20-08",
	"v17",
	"use saashq.tests.utils.make_test_records_for_doctype",
)
def test_runner_make_test_records_for_doctype(*args, **kwargs):
	from saashq.tests.utils import make_test_records_for_doctype

	return make_test_records_for_doctype(*args, **kwargs)


@deprecated(
	"saashq.tests_runner.print_mandatory_fields",
	"2024-20-08",
	"v17",
	"no public api anymore",
)
def test_runner_print_mandatory_fields(*args, **kwargs):
	from saashq.tests.utils.generators import print_mandatory_fields

	return print_mandatory_fields(*args, **kwargs)


@deprecated(
	"saashq.tests_runner.get_test_record_log",
	"2024-20-08",
	"v17",
	"no public api anymore",
)
def test_runner_get_test_record_log(doctype):
	from saashq.tests.utils.generators import TestRecordManager

	return TestRecordManager().get(doctype)


@deprecated(
	"saashq.tests_runner.add_to_test_record_log",
	"2024-20-08",
	"v17",
	"no public api anymore",
)
def test_runner_add_to_test_record_log(doctype):
	from saashq.tests.utils.generators import TestRecordManager

	return TestRecordManager().add(doctype)


@deprecated(
	"saashq.tests_runner.main",
	"2024-20-08",
	"v17",
	"no public api anymore",
)
def test_runner_main(*args, **kwargs):
	from saashq.orgmands.testing import main

	return main(*args, **kwargs)


@deprecated(
	"saashq.tests_runner.xmlrunner_wrapper",
	"2024-20-08",
	"v17",
	"no public api anymore",
)
def test_xmlrunner_wrapper(output):
	"""Convenience wrapper to keep method signature unchanged for XMLTestRunner and TextTestRunner"""
	try:
		import xmlrunner
	except ImportError:
		print("Development dependencies are required to execute this command. To install run:")
		print("$ wrench setup requirements --dev")
		raise

	def _runner(*args, **kwargs):
		kwargs["output"] = output
		return xmlrunner.XMLTestRunner(*args, **kwargs)

	return _runner


@deprecated(
	"saashq.tests.upate_system_settings",
	"2024-20-08",
	"v17",
	"use with `self.change_settings(...):` context manager",
)
def tests_update_system_settings(args, commit=False):
	import saashq

	doc = saashq.get_doc("System Settings")
	doc.update(args)
	doc.flags.ignore_mandatory = 1
	doc.save()
	if commit:
		# moved here
		saashq.db.commit()  # nosemgrep


@deprecated(
	"saashq.tests.get_system_setting",
	"2024-20-08",
	"v17",
	"use `saashq.db.get_single_value('System Settings', key)`",
)
def tests_get_system_setting(key):
	import saashq

	return saashq.db.get_single_value("System Settings", key)


@deprecated(
	"saashq.tests.utils.change_settings",
	"2024-20-08",
	"v17",
	"use `saashq.tests.change_settings` or the cls.change_settings",
)
def tests_change_settings(*args, **kwargs):
	from saashq.tests.classes.context_managers import change_settings

	return change_settings(*args, **kwargs)


@deprecated(
	"saashq.tests.utils.patch_hooks",
	"2024-20-08",
	"v17",
	"use `saashq.tests.patch_hooks` or the cls.patch_hooks",
)
def tests_patch_hooks(*args, **kwargs):
	from saashq.tests.classes.context_managers import patch_hooks

	return patch_hooks(*args, **kwargs)


@deprecated(
	"saashq.tests.utils.debug_on",
	"2024-20-08",
	"v17",
	"use `saashq.tests.debug_on` or the cls.debug_on",
)
def tests_debug_on(*args, **kwargs):
	from saashq.tests.classes.context_managers import debug_on

	return debug_on(*args, **kwargs)


@deprecated(
	"saashq.tests.utils.timeout",
	"2024-20-08",
	"v17",
	"use `saashq.tests.timeout` or the cls.timeout",
)
def tests_timeout(*args, **kwargs):
	from saashq.tests.classes.context_managers import timeout

	return timeout(*args, **kwargs)


def get_tests_SaashqTestCase():
	class CompatSaashqTestCase:
		def __new__(cls, *args, **kwargs):
			from saashq.tests import IntegrationTestCase

			class _CompatSaashqTestCase(IntegrationTestCase):
				def __init__(self, *args, **kwargs):
					deprecation_warning(
						"2024-20-08",
						"v17",
						"Import `saashq.tests.UnitTestCase` or `saashq.tests.IntegrationTestCase` respectively instead of `saashq.tests.utils.SaashqTestCase`",
					)
					super().__init__(*args, **kwargs)

			return _CompatSaashqTestCase(*args, **kwargs)

	return CompatSaashqTestCase


def get_tests_IntegrationTestCase():
	class CompatIntegrationTestCase:
		def __new__(cls, *args, **kwargs):
			from saashq.tests import IntegrationTestCase

			class _CompatIntegrationTestCase(IntegrationTestCase):
				def __init__(self, *args, **kwargs):
					deprecation_warning(
						"2024-20-08",
						"v17",
						"Import `saashq.tests.IntegrationTestCase` instead of `saashq.tests.utils.IntegrationTestCase`",
					)
					super().__init__(*args, **kwargs)

			return _CompatIntegrationTestCase(*args, **kwargs)

	return CompatIntegrationTestCase


def get_tests_UnitTestCase():
	class CompatUnitTestCase:
		def __new__(cls, *args, **kwargs):
			from saashq.tests import UnitTestCase

			class _CompatUnitTestCase(UnitTestCase):
				def __init__(self, *args, **kwargs):
					deprecation_warning(
						"2024-20-08",
						"v17",
						"Import `saashq.tests.UnitTestCase` instead of `saashq.tests.utils.UnitTestCase`",
					)
					super().__init__(*args, **kwargs)

			return _CompatUnitTestCase(*args, **kwargs)

	return CompatUnitTestCase


@deprecated(
	"saashq.model.trace.traced_field_context",
	"2024-20-08",
	"v17",
	"use `cls.trace_fields`",
)
def model_trace_traced_field_context(*args, **kwargs):
	from saashq.tests.classes.context_managers import trace_fields

	return trace_fields(*args, **kwargs)


@deprecated(
	"saashq.tests.utils.get_dependencies",
	"2024-20-09",
	"v17",
	"refactor to use saashq.tests.utils.get_missing_records_doctypes",
)
def tests_utils_get_dependencies(doctype):
	"""Get the dependencies for the specified doctype"""
	import saashq
	from saashq.tests.utils.generators import get_modules

	module, test_module = get_modules(doctype)
	meta = saashq.get_meta(doctype)
	link_fields = meta.get_link_fields()

	for df in meta.get_table_fields():
		link_fields.extend(saashq.get_meta(df.options).get_link_fields())

	options_list = [df.options for df in link_fields]

	if hasattr(test_module, "test_dependencies"):
		options_list += test_module.test_dependencies

	options_list = list(set(options_list))

	if hasattr(test_module, "test_ignore"):
		for doctype_name in test_module.test_ignore:
			if doctype_name in options_list:
				options_list.remove(doctype_name)

	options_list.sort()

	return options_list


@deprecated(
	"saashq.tests_runner.get_dependencies",
	"2024-20-08",
	"v17",
	"refactor to use saashq.tests.utils.get_missing_record_doctypes",
)
def test_runner_get_dependencies(doctype):
	return tests_utils_get_dependencies(doctype)


@deprecated(
	"saashq.get_test_records",
	"2024-20-09",
	"v17",
	"""Please access the global test records pool via cls.globalTestRecords['Some Doc'] -> list.
If not an IntegrationTestCase, use saashq.tests.utils.load_test_records_for (check return type).
""",
)
def saashq_get_test_records(doctype):
	import saashq
	from saashq.tests.utils.generators import load_test_records_for

	saashq.flags.deprecation_dumpster_invoked = True

	records = load_test_records_for(doctype)
	if isinstance(records, dict):
		_records = []
		for doctype, docs in records.items():
			for doc in docs:
				_doc = doc.copy()
				_doc["doctype"] = doctype
				_records.append(_doc)
		return _records
	return records
