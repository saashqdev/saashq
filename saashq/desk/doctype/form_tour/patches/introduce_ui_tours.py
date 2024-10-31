import json

import saashq


def execute():
	"""Handle introduction of UI tours"""
	completed = {}
	for tour in saashq.get_all("Form Tour", {"ui_tour": 1}, pluck="name"):
		completed[tour] = {"is_complete": True}

	User = saashq.qb.DocType("User")
	saashq.qb.update(User).set("onboarding_status", json.dumps(completed)).run()
