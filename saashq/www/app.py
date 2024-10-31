# Copyright (c) 2015, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import os

no_cache = 1

import json
import re
from urllib.parse import urlencode

import saashq
import saashq.sessions
from saashq import _
from saashq.utils.jinja_globals import is_rtl

SCRIPT_TAG_PATTERN = re.compile(r"\<script[^<]*\</script\>")
CLOSING_SCRIPT_TAG_PATTERN = re.compile(r"</script\>")


def get_context(context):
	if saashq.session.user == "Guest":
		saashq.response["status_code"] = 403
		saashq.msgprint(_("Log in to access this page."))
		saashq.redirect(f"/login?{urlencode({'redirect-to': saashq.request.path})}")

	elif saashq.db.get_value("User", saashq.session.user, "user_type", order_by=None) == "Website User":
		saashq.throw(_("You are not permitted to access this page."), saashq.PermissionError)

	try:
		boot = saashq.sessions.get()
	except Exception as e:
		raise saashq.SessionBootFailed from e

	# this needs commit
	csrf_token = saashq.sessions.get_csrf_token()

	saashq.db.commit()

	boot_json = saashq.as_json(boot, indent=None, separators=(",", ":"))

	# remove script tags from boot
	boot_json = SCRIPT_TAG_PATTERN.sub("", boot_json)

	# TODO: Find better fix
	boot_json = CLOSING_SCRIPT_TAG_PATTERN.sub("", boot_json)
	boot_json = json.dumps(boot_json)

	hooks = saashq.get_hooks()
	app_include_js = hooks.get("app_include_js", []) + saashq.conf.get("app_include_js", [])
	app_include_css = hooks.get("app_include_css", []) + saashq.conf.get("app_include_css", [])
	app_include_icons = hooks.get("app_include_icons", [])

	if saashq.get_system_settings("enable_telemetry") and os.getenv("SAASHQ_SENTRY_DSN"):
		app_include_js.append("sentry.bundle.js")

	context.update(
		{
			"no_cache": 1,
			"build_version": saashq.utils.get_build_version(),
			"app_include_js": app_include_js,
			"app_include_css": app_include_css,
			"app_include_icons": app_include_icons,
			"layout_direction": "rtl" if is_rtl() else "ltr",
			"lang": saashq.local.lang,
			"sounds": hooks["sounds"],
			"boot": boot if context.get("for_mobile") else boot_json,
			"desk_theme": boot.get("desk_theme") or "Light",
			"csrf_token": csrf_token,
			"google_analytics_id": saashq.conf.get("google_analytics_id"),
			"google_analytics_anonymize_ip": saashq.conf.get("google_analytics_anonymize_ip"),
			"app_name": (
				saashq.get_website_settings("app_name") or saashq.get_system_settings("app_name") or "Saashq"
			),
		}
	)

	return context
