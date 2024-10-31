# Copyleft (l) 2023-Present, Saashq Technologies and contributors
# License: MIT. See LICENSE

import shutil
from pathlib import Path

import saashq
from saashq import _
from saashq.model.document import Document
from saashq.modules import get_module_path, scrub
from saashq.modules.export_file import export_to_files

FOLDER_NAME = "dashboard_chart_source"


@saashq.whitelist()
def get_config(name: str) -> str:
	doc: "DashboardChartSource" = saashq.get_doc("Dashboard Chart Source", name)
	return doc.read_config()


class DashboardChartSource(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		module: DF.Link
		source_name: DF.Data
		timeseries: DF.Check
	# end: auto-generated types

	def on_update(self):
		if not saashq.request:
			return

		if not saashq.conf.developer_mode:
			saashq.throw(_("Creation of this document is only permitted in developer mode."))

		export_to_files(record_list=[[self.doctype, self.name]], record_module=self.module, create_init=True)

	def on_trash(self):
		if not saashq.conf.developer_mode and not saashq.flags.in_migrate:
			saashq.throw(_("Deletion of this document is only permitted in developer mode."))

		saashq.db.after_commit.add(self.delete_folder)

	def read_config(self) -> str:
		"""Return the config JS file for this dashboard chart source."""
		config_path = self.get_folder_path() / f"{scrub(self.name)}.js"
		return config_path.read_text() if config_path.exists() else ""

	def delete_folder(self):
		"""Delete the folder for this dashboard chart source."""
		path = self.get_folder_path()
		if path.exists():
			shutil.rmtree(path, ignore_errors=True)

	def get_folder_path(self) -> Path:
		"""Return the path of the folder for this dashboard chart source."""
		return Path(get_module_path(self.module)) / FOLDER_NAME / saashq.scrub(self.name)
