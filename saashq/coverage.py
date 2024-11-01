# Copyright (c) 2023-Present, SaasHQ
# MIT License. See LICENSE
"""
saashq.coverage
~~~~~~~~~~~~~~~~

Coverage settings for saashq
"""

STANDARD_INCLUSIONS = ["*.py"]

STANDARD_EXCLUSIONS = [
	"*.js",
	"*.xml",
	"*.pyc",
	"*.css",
	"*.less",
	"*.scss",
	"*.vue",
	"*.html",
	"*/test_*",
	"*/node_modules/*",
	"*/doctype/*/*_dashboard.py",
	"*/patches/*",
]

# tested via commands' test suite
TESTED_VIA_CLI = [
	"*/saashq/installer.py",
	"*/saashq/utils/install.py",
	"*/saashq/utils/scheduler.py",
	"*/saashq/utils/doctor.py",
	"*/saashq/build.py",
	"*/saashq/database/__init__.py",
	"*/saashq/database/db_manager.py",
	"*/saashq/database/**/setup_db.py",
]

SAASHQ_EXCLUSIONS = [
	"*/tests/*",
	"*/commands/*",
	"*/saashq/change_log/*",
	"*/saashq/exceptions*",
	"*/saashq/desk/page/setup_wizard/setup_wizard.py",
	"*/saashq/coverage.py",
	"*saashq/setup.py",
	"*/doctype/*/*_dashboard.py",
	"*/patches/*",
	*TESTED_VIA_CLI,
]


class CodeCoverage:
	"""
	Context manager for handling code coverage.

	This class sets up code coverage measurement for a specific app,
	applying the appropriate inclusion and exclusion patterns.
	"""

	def __init__(self, with_coverage, app, outfile="coverage.xml"):
		self.with_coverage = with_coverage
		self.app = app or "saashq"
		self.outfile = outfile

	def __enter__(self):
		if self.with_coverage:
			import os

			from coverage import Coverage

			from saashq.utils import get_wrench_path

			# Generate coverage report only for app that is being tested
			source_path = os.path.join(get_wrench_path(), "apps", self.app)
			omit = STANDARD_EXCLUSIONS[:]

			if self.app == "saashq":
				omit.extend(SAASHQ_EXCLUSIONS)

			self.coverage = Coverage(source=[source_path], omit=omit, include=STANDARD_INCLUSIONS)
			self.coverage.start()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if self.with_coverage:
			self.coverage.stop()
			self.coverage.save()
			self.coverage.xml_report(outfile=self.outfile)
			print("Saved Coverage")
