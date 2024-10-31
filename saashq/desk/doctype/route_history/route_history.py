# Copyleft (l) 2023-Present, Saashq Technologies and contributors
# License: MIT. See LICENSE

import saashq
from saashq.deferred_insert import deferred_insert as _deferred_insert
from saashq.model.document import Document


class RouteHistory(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		route: DF.Data | None
		user: DF.Link | None
	# end: auto-generated types

	@staticmethod
	def clear_old_logs(days=30):
		from saashq.query_builder import Interval
		from saashq.query_builder.functions import Now

		table = saashq.qb.DocType("Route History")
		saashq.db.delete(table, filters=(table.creation < (Now() - Interval(days=days))))


@saashq.whitelist()
def deferred_insert(routes):
	routes = [
		{
			"user": saashq.session.user,
			"route": route.get("route"),
			"creation": route.get("creation"),
		}
		for route in saashq.parse_json(routes)
	]

	_deferred_insert("Route History", routes)


@saashq.whitelist()
def frequently_visited_links():
	return saashq.get_all(
		"Route History",
		fields=["route", "count(name) as count"],
		filters={"user": saashq.session.user},
		group_by="route",
		order_by="count desc",
		limit=5,
	)
