import json

import saashq


def execute():
	if saashq.db.exists("Social Login Key", "github"):
		saashq.db.set_value(
			"Social Login Key", "github", "auth_url_data", json.dumps({"scope": "user:email"})
		)
