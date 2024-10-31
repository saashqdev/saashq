""" Basic telemetry for improving apps.

WARNING: Everything in this file should be treated "internal" and is subjected to change or get
removed without any warning.
"""
from contextlib import suppress

import saashq
from saashq.utils import getdate
from saashq.utils.caching import site_cache

from posthog import Posthog  # isort: skip

POSTHOG_PROJECT_FIELD = "posthog_project_id"
POSTHOG_HOST_FIELD = "posthog_host"


def add_bootinfo(bootinfo):
	bootinfo.telemetry_site_age = site_age()

	if not saashq.get_system_settings("enable_telemetry"):
		return

	bootinfo.enable_telemetry = True
	bootinfo.posthog_host = saashq.conf.get(POSTHOG_HOST_FIELD)
	bootinfo.posthog_project_id = saashq.conf.get(POSTHOG_PROJECT_FIELD)


@site_cache(ttl=60 * 60 * 12)
def site_age():
	try:
		est_creation = saashq.db.get_value("User", "Administrator", "creation")
		return (getdate() - getdate(est_creation)).days + 1
	except Exception:
		pass


def init_telemetry():
	"""Init posthog for server side telemetry."""
	if hasattr(saashq.local, "posthog"):
		return

	if not saashq.get_system_settings("enable_telemetry"):
		return

	posthog_host = saashq.conf.get(POSTHOG_HOST_FIELD)
	posthog_project_id = saashq.conf.get(POSTHOG_PROJECT_FIELD)

	if not posthog_host or not posthog_project_id:
		return

	with suppress(Exception):
		saashq.local.posthog = Posthog(posthog_project_id, host=posthog_host)


def capture(event, app, **kwargs):
	init_telemetry()
	ph: Posthog = getattr(saashq.local, "posthog", None)
	with suppress(Exception):
		ph and ph.capture(distinct_id=saashq.local.site, event=f"{app}_{event}", **kwargs)


def capture_doc(doc, action):
	with suppress(Exception):
		age = site_age()
		if not age or age > 15:
			return

		if doc.get("__islocal") or not doc.get("name"):
			capture("document_created", "saashq", properties={"doctype": doc.doctype, "action": "Insert"})
		else:
			capture("document_modified", "saashq", properties={"doctype": doc.doctype, "action": action})
