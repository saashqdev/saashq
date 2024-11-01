# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import json

import saashq
from saashq.model.document import Document
from saashq.utils.safe_exec import read_sql, safe_exec


class SystemConsole(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		commit: DF.Check
		console: DF.Code | None
		output: DF.Code | None
		show_processlist: DF.Check
		type: DF.Literal["Python", "SQL"]
	# end: auto-generated types

	def run(self):
		saashq.only_for("System Manager")
		try:
			saashq.local.debug_log = []
			if self.type == "Python":
				safe_exec(self.console, script_filename="System Console")
				self.output = "\n".join(saashq.debug_log)
			elif self.type == "SQL":
				self.output = saashq.as_json(read_sql(self.console, as_dict=1))
		except Exception:
			self.commit = False
			self.output = saashq.get_traceback()

		if self.commit:
			saashq.db.commit()
		else:
			saashq.db.rollback()
		saashq.get_doc(
			doctype="Console Log", script=self.console, type=self.type, committed=self.commit
		).insert()
		saashq.db.commit()


@saashq.whitelist()
def execute_code(doc):
	console = saashq.get_doc(json.loads(doc))
	console.run()
	return console.as_dict()


@saashq.whitelist()
def show_processlist():
	saashq.only_for("System Manager")
	return _show_processlist()


def _show_processlist():
	return saashq.db.multisql(
		{
			"postgres": """
			SELECT pid AS "Id",
				query_start AS "Time",
				state AS "State",
				query AS "Info",
				wait_event AS "Progress"
			FROM pg_stat_activity""",
			"mariadb": "show full processlist",
		},
		as_dict=True,
	)
