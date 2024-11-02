# Copyright (c) 2021, Saashq Technologies and contributors
# For license information, please see license.txt

import os
import subprocess

import saashq
from saashq.model.document import Document
from saashq.modules.export_file import export_doc
from saashq.query_builder.functions import Max


class PackageRelease(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		major: DF.Int
		minor: DF.Int
		package: DF.Link
		patch: DF.Int
		path: DF.SmallText | None
		publish: DF.Check
		release_notes: DF.MarkdownEditor | None
	# end: auto-generated types

	def set_version(self):
		# set the next patch release by default
		doctype = saashq.qb.DocType("Package Release")
		if not self.major:
			self.major = (
				saashq.qb.from_(doctype)
				.where(doctype.package == self.package)
				.select(Max(doctype.minor))
				.run()[0][0]
				or 0
			)

		if not self.minor:
			self.minor = (
				saashq.qb.from_(doctype)
				.where(doctype.package == self.package)
				.select(Max("minor"))
				.run()[0][0]
				or 0
			)
		if not self.patch:
			value = (
				saashq.qb.from_(doctype)
				.where(doctype.package == self.package)
				.select(Max("patch"))
				.run()[0][0]
				or 0
			)
			self.patch = value + 1

	def autoname(self):
		self.set_version()
		self.name = "{}-{}.{}.{}".format(
			saashq.db.get_value("Package", self.package, "package_name"), self.major, self.minor, self.patch
		)

	def validate(self):
		if self.publish:
			self.export_files()

	def export_files(self):
		"""Export all the documents in this package to site/packages folder"""
		package = saashq.get_doc("Package", self.package)

		self.export_modules()
		self.export_package_files(package)
		self.make_tarfile(package)

	def export_modules(self):
		for m in saashq.get_all("Module Def", dict(package=self.package)):
			module = saashq.get_doc("Module Def", m.name)
			for l in module.meta.links:
				if l.link_doctype == "Module Def":
					continue
				# all documents of the type in the module
				for d in saashq.get_all(l.link_doctype, dict(module=m.name)):
					export_doc(saashq.get_doc(l.link_doctype, d.name))

	def export_package_files(self, package):
		# write readme
		with open(saashq.get_site_path("packages", package.package_name, "README.md"), "w") as readme:
			readme.write(package.readme)

		# write license
		if package.license:
			with open(saashq.get_site_path("packages", package.package_name, "LICENSE.md"), "w") as license:
				license.write(package.license)

		# write package.json as `saashq_package.json`
		with open(
			saashq.get_site_path("packages", package.package_name, package.package_name + ".json"), "w"
		) as packagefile:
			packagefile.write(saashq.as_json(package.as_dict(no_nulls=True)))

	def make_tarfile(self, package):
		# make tarfile
		filename = f"{self.name}.tar.gz"
		subprocess.check_output(
			["tar", "czf", filename, package.package_name], cwd=saashq.get_site_path("packages")
		)

		# move file
		subprocess.check_output(
			["mv", saashq.get_site_path("packages", filename), saashq.get_site_path("public", "files")]
		)

		# make attachment
		file = saashq.get_doc(
			doctype="File",
			file_url="/" + os.path.join("files", filename),
			attached_to_doctype=self.doctype,
			attached_to_name=self.name,
		)

		# Set path to tarball
		self.path = file.file_url

		file.flags.ignore_duplicate_entry_error = True
		file.insert()
