import re

import saashq
from saashq.query_builder import DocType


def execute():
	"""Replace temporarily available Database Aggregate APIs on saashq (develop)

	APIs changed:
	        * saashq.db.max => saashq.qb.max
	        * saashq.db.min => saashq.qb.min
	        * saashq.db.sum => saashq.qb.sum
	        * saashq.db.avg => saashq.qb.avg
	"""
	ServerScript = DocType("Server Script")
	server_scripts = (
		saashq.qb.from_(ServerScript)
		.where(
			ServerScript.script.like("%saashq.db.max(%")
			| ServerScript.script.like("%saashq.db.min(%")
			| ServerScript.script.like("%saashq.db.sum(%")
			| ServerScript.script.like("%saashq.db.avg(%")
		)
		.select("name", "script")
		.run(as_dict=True)
	)

	for server_script in server_scripts:
		name, script = server_script["name"], server_script["script"]

		for agg in ["avg", "max", "min", "sum"]:
			script = re.sub(f"saashq.db.{agg}\\(", f"saashq.qb.{agg}(", script)

		saashq.db.set_value("Server Script", name, "script", script)
