# Copyright (c) 2022, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import contextlib
import functools
import json
import os
from textwrap import dedent

import saashq
import saashq.model.sync
import saashq.modules.patch_handler
import saashq.translate
from saashq.cache_manager import clear_global_cache
from saashq.core.doctype.language.language import sync_languages
from saashq.core.doctype.navbar_settings.navbar_settings import sync_standard_items
from saashq.core.doctype.scheduled_job_type.scheduled_job_type import sync_jobs
from saashq.database.schema import add_column
from saashq.deferred_insert import save_to_db as flush_deferred_inserts
from saashq.desk.notifications import clear_notifications
from saashq.modules.patch_handler import PatchType
from saashq.modules.utils import sync_customizations
from saashq.search.website_search import build_index_for_all_routes
from saashq.utils.connections import check_connection
from saashq.utils.dashboard import sync_dashboards
from saashq.utils.fixtures import sync_fixtures
from saashq.website.utils import clear_website_cache

BENCH_START_MESSAGE = dedent(
	"""
	Cannot run bench migrate without the services running.
	If you are running bench in development mode, make sure that bench is running:

	$ bench start

	Otherwise, check the server logs and ensure that all the required services are running.
	"""
)


def atomic(method):
	@functools.wraps(method)
	def wrapper(*args, **kwargs):
		try:
			ret = method(*args, **kwargs)
			saashq.db.commit()
			return ret
		except Exception as e:
			# database itself can be gone while attempting rollback.
			# We should preserve original exception in this case.
			with contextlib.suppress(Exception):
				saashq.db.rollback()
			raise e

	return wrapper


class SiteMigration:
	"""Migrate all apps to the current version, will:
	- run before migrate hooks
	- run patches
	- sync doctypes (schema)
	- sync dashboards
	- sync jobs
	- sync fixtures
	- sync customizations
	- sync languages
	- sync web pages (from /www)
	- run after migrate hooks
	"""

	def __init__(self, skip_failing: bool = False, skip_search_index: bool = False) -> None:
		self.skip_failing = skip_failing
		self.skip_search_index = skip_search_index

	def setUp(self):
		"""Complete setup required for site migration"""
		saashq.flags.touched_tables = set()
		self.touched_tables_file = saashq.get_site_path("touched_tables.json")
		saashq.clear_cache()
		add_column(doctype="DocType", column_name="migration_hash", fieldtype="Data")
		clear_global_cache()

		if os.path.exists(self.touched_tables_file):
			os.remove(self.touched_tables_file)

		saashq.flags.in_migrate = True

	def tearDown(self):
		"""Run operations that should be run post schema updation processes
		This should be executed irrespective of outcome
		"""
		saashq.translate.clear_cache()
		clear_website_cache()
		clear_notifications()

		with open(self.touched_tables_file, "w") as f:
			json.dump(list(saashq.flags.touched_tables), f, sort_keys=True, indent=4)

		if not self.skip_search_index:
			print(f"Queued rebuilding of search index for {saashq.local.site}")
			saashq.enqueue(build_index_for_all_routes, queue="long")

		saashq.publish_realtime("version-update")
		saashq.flags.touched_tables.clear()
		saashq.flags.in_migrate = False

	@atomic
	def pre_schema_updates(self):
		"""Executes `before_migrate` hooks"""
		for app in saashq.get_installed_apps():
			for fn in saashq.get_hooks("before_migrate", app_name=app):
				saashq.get_attr(fn)()

	@atomic
	def run_schema_updates(self):
		"""Run patches as defined in patches.txt, sync schema changes as defined in the {doctype}.json files"""
		saashq.modules.patch_handler.run_all(
			skip_failing=self.skip_failing, patch_type=PatchType.pre_model_sync
		)
		saashq.model.sync.sync_all()
		saashq.modules.patch_handler.run_all(
			skip_failing=self.skip_failing, patch_type=PatchType.post_model_sync
		)

	@atomic
	def post_schema_updates(self):
		"""Execute pending migration tasks post patches execution & schema sync
		This includes:
		* Sync `Scheduled Job Type` and scheduler events defined in hooks
		* Sync fixtures & custom scripts
		* Sync in-Desk Module Dashboards
		* Sync customizations: Custom Fields, Property Setters, Custom Permissions
		* Sync Saashq's internal language master
		* Flush deferred inserts made during maintenance mode.
		* Sync Portal Menu Items
		* Sync Installed Applications Version History
		* Execute `after_migrate` hooks
		"""
		print("Syncing jobs...")
		sync_jobs()

		print("Syncing fixtures...")
		sync_fixtures()
		sync_standard_items()

		print("Syncing dashboards...")
		sync_dashboards()

		print("Syncing customizations...")
		sync_customizations()

		print("Syncing languages...")
		sync_languages()

		print("Flushing deferred inserts...")
		flush_deferred_inserts()

		print("Removing orphan doctypes...")
		saashq.model.sync.remove_orphan_doctypes()

		print("Syncing portal menu...")
		saashq.get_single("Portal Settings").sync_menu()

		print("Updating installed applications...")
		saashq.get_single("Installed Applications").update_versions()

		print("Executing `after_migrate` hooks...")
		for app in saashq.get_installed_apps():
			for fn in saashq.get_hooks("after_migrate", app_name=app):
				saashq.get_attr(fn)()

	def required_services_running(self) -> bool:
		"""Return True if all required services are running. Return False and print
		instructions to stdout when required services are not available.
		"""
		service_status = check_connection(redis_services=["redis_cache"])
		are_services_running = all(service_status.values())

		if not are_services_running:
			for service in service_status:
				if not service_status.get(service, True):
					print(f"Service {service} is not running.")
			print(BENCH_START_MESSAGE)

		return are_services_running

	def run(self, site: str):
		"""Run Migrate operation on site specified. This method initializes
		and destroys connections to the site database.
		"""
		from saashq.utils.synchronization import filelock

		if site:
			saashq.init(site)
			saashq.connect()

		if not self.required_services_running():
			raise SystemExit(1)

		with filelock("bench_migrate", timeout=1):
			self.setUp()
			try:
				self.pre_schema_updates()
				self.run_schema_updates()
				self.post_schema_updates()
			finally:
				self.tearDown()
				saashq.destroy()
