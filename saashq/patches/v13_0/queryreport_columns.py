# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import json

import saashq


def execute():
	"""Convert Query Report json to support other content."""
	records = saashq.get_all("Report", filters={"json": ["!=", ""]}, fields=["name", "json"])
	for record in records:
		jstr = record["json"]
		data = json.loads(jstr)
		if isinstance(data, list):
			# double escape braces
			jstr = f'{{"columns":{jstr}}}'
			saashq.db.set_value("Report", record["name"], "json", jstr)
