# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import json
import os
from pathlib import Path

import saashq
from saashq.model.document import Document
from saashq.modules.export_file import delete_folder


class ModuleDef(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		app_name: DF.Literal[None]
		custom: DF.Check
		module_name: DF.Data
		package: DF.Link | None
		restrict_to_domain: DF.Link | None
	# end: auto-generated types

	def validate(self):
		from saashq.modules.utils import get_module_app

		if not self.app_name and not self.custom:
			self.app_name = get_module_app(self.name)

	def on_update(self):
		"""If in `developer_mode`, create folder for module and
		add in `modules.txt` of app if missing."""
		saashq.clear_cache()
		if not self.custom and saashq.conf.get("developer_mode"):
			self.create_modules_folder()
			self.add_to_modules_txt()

	def create_modules_folder(self):
		"""Creates a folder `[app]/[module]` and adds `__init__.py`"""
		module_path = saashq.get_app_path(self.app_name, self.name)
		if not os.path.exists(module_path):
			os.mkdir(module_path)
			with open(os.path.join(module_path, "__init__.py"), "w") as f:
				f.write("")

	def add_to_modules_txt(self):
		"""Adds to `[app]/modules.txt`"""
		modules = None
		if not saashq.local.module_app.get(saashq.scrub(self.name)):
			with open(saashq.get_app_path(self.app_name, "modules.txt")) as f:
				content = f.read()
				if self.name not in content.splitlines():
					modules = list(filter(None, content.splitlines()))
					modules.append(self.name)

			if modules:
				with open(saashq.get_app_path(self.app_name, "modules.txt"), "w") as f:
					f.write("\n".join(modules))

				saashq.clear_cache()
				saashq.setup_module_map()

	def on_trash(self):
		"""Delete module name from modules.txt"""

		if not saashq.conf.get("developer_mode") or saashq.flags.in_uninstall or self.custom:
			return

		if saashq.local.module_app.get(saashq.scrub(self.name)):
			saashq.db.after_commit.add(self.delete_module_from_file)

	def delete_module_from_file(self):
		delete_folder(self.module_name, "Module Def", self.name)
		modules = []

		modules_txt = Path(saashq.get_app_path(self.app_name, "modules.txt"))
		modules = [m for m in modules_txt.read_text().splitlines() if m]

		if self.name in modules:
			modules.remove(self.name)

		if modules:
			modules_txt.write_text("\n".join(modules))
			saashq.clear_cache()
			saashq.setup_module_map()


@saashq.whitelist()
def get_installed_apps():
	return json.dumps(saashq.get_installed_apps())
