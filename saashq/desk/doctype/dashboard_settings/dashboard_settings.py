# Copyright (c) 2020, Saashq Technologies and contributors
# License: MIT. See LICENSE

import json

import saashq

# import saashq
from saashq.model.document import Document


class DashboardSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		chart_config: DF.Code | None
		user: DF.Link | None
	# end: auto-generated types

	pass


@saashq.whitelist()
def create_dashboard_settings(user):
	if not saashq.db.exists("Dashboard Settings", user):
		doc = saashq.new_doc("Dashboard Settings")
		doc.name = user
		doc.insert(ignore_permissions=True)
		saashq.db.commit()
		return doc


def get_permission_query_conditions(user):
	if not user:
		user = saashq.session.user

	return f"""(`tabDashboard Settings`.name = {saashq.db.escape(user)})"""


@saashq.whitelist()
def save_chart_config(reset, config, chart_name):
	reset = saashq.parse_json(reset)
	doc = saashq.get_doc("Dashboard Settings", saashq.session.user)
	chart_config = saashq.parse_json(doc.chart_config) or {}

	if reset:
		chart_config[chart_name] = {}
	else:
		config = saashq.parse_json(config)
		if chart_name not in chart_config:
			chart_config[chart_name] = {}
		chart_config[chart_name].update(config)

	saashq.db.set_value("Dashboard Settings", saashq.session.user, "chart_config", json.dumps(chart_config))
