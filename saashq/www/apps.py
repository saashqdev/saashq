# Copyright (c) 2023, SaasHQ
# MIT License. See license.txt

import saashq
from saashq import _
from saashq.apps import get_apps


def get_context():
	all_apps = get_apps()

	system_default_app = saashq.get_system_settings("default_app")
	user_default_app = saashq.db.get_value("User", saashq.session.user, "default_app")
	default_app = user_default_app if user_default_app else system_default_app

	if len(all_apps) == 0:
		saashq.local.flags.redirect_location = "/app"
		raise saashq.Redirect

	for app in all_apps:
		app["is_default"] = True if app.get("name") == default_app else False

	return {"apps": all_apps}
