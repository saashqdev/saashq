# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import re

import saashq
from saashq import _
from saashq.defaults import clear_default, set_default
from saashq.model.document import Document


class Language(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		based_on: DF.Link | None
		date_format: DF.Literal[
			"", "yyyy-mm-dd", "dd-mm-yyyy", "dd/mm/yyyy", "dd.mm.yyyy", "mm/dd/yyyy", "mm-dd-yyyy"
		]
		enabled: DF.Check
		first_day_of_the_week: DF.Literal[
			"", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
		]
		flag: DF.Data | None
		language_code: DF.Data
		language_name: DF.Data
		number_format: DF.Literal[
			"",
			"#,###.##",
			"#.###,##",
			"# ###.##",
			"# ###,##",
			"#'###.##",
			"#, ###.##",
			"#,##,###.##",
			"#,###.###",
			"#.###",
			"#,###",
		]
		time_format: DF.Literal["", "HH:mm:ss", "HH:mm"]
	# end: auto-generated types

	def validate(self):
		validate_with_regex(self.language_code, "Language Code")

	def before_rename(self, old, new, merge=False):
		validate_with_regex(new, "Name")

	def on_update(self):
		saashq.cache.delete_value("languages_with_name")
		saashq.cache.delete_value("languages")
		self.update_user_defaults()

	def update_user_defaults(self):
		"""Update user defaults for date, time, number format and first day of the week.

		When we change any settings of a language, the defaults for all users with that language
		should be updated.
		"""
		users = saashq.get_all("User", filters={"language": self.name}, pluck="name")
		for key in ("date_format", "time_format", "number_format", "first_day_of_the_week"):
			if self.has_value_changed(key):
				for user in users:
					if new_value := self.get(key):
						set_default(key, new_value, user)
					else:
						clear_default(key, parent=user)


def validate_with_regex(name, label):
	pattern = re.compile("^[a-zA-Z]+[-_]*[a-zA-Z]+$")
	if not pattern.match(name):
		saashq.throw(
			_(
				"""{0} must begin and end with a letter and can only contain letters, hyphen or underscore."""
			).format(label)
		)


def sync_languages():
	"""Create Language records from saashq/geo/languages.csv"""
	from csv import DictReader

	with open(saashq.get_app_path("saashq", "geo", "languages.csv")) as f:
		reader = DictReader(f)
		for row in reader:
			if not saashq.db.exists("Language", row["language_code"]):
				doc = saashq.new_doc("Language")
				doc.update(row)
				doc.insert()
