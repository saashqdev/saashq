# Copyright (c) 2019, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import os
from functools import wraps
from os.path import join

import saashq
from saashq import _
from saashq.modules.import_file import import_file_by_path
from saashq.utils import cint, get_link_to_form


def cache_source(function):
	@wraps(function)
	def wrapper(*args, **kwargs):
		if kwargs.get("chart_name"):
			chart = saashq.get_doc("Dashboard Chart", kwargs.get("chart_name"))
		else:
			chart = kwargs.get("chart")
		no_cache = kwargs.get("no_cache")
		if no_cache:
			return function(chart=chart, no_cache=no_cache)
		chart_name = saashq.parse_json(chart).name
		cache_key = f"chart-data:{chart_name}"
		if cint(kwargs.get("refresh")):
			results = generate_and_cache_results(kwargs, function, cache_key, chart)
		else:
			cached_results = saashq.cache.get_value(cache_key)
			if cached_results:
				results = saashq.parse_json(saashq.safe_decode(cached_results))
			else:
				results = generate_and_cache_results(kwargs, function, cache_key, chart)
		return results

	return wrapper


def generate_and_cache_results(args, function, cache_key, chart):
	try:
		args = saashq._dict(args)
		results = function(
			chart_name=args.chart_name,
			filters=args.filters or None,
			from_date=args.from_date or None,
			to_date=args.to_date or None,
			time_interval=args.time_interval or None,
			timespan=args.timespan or None,
			heatmap_year=args.heatmap_year or None,
		)
	except TypeError as e:
		if str(e) == "'NoneType' object is not iterable":
			# Probably because of invalid link filter
			#
			# Note: Do not try to find the right way of doing this because
			# it results in an inelegant & inefficient solution
			# ref: https://github.com/saashq/saashq/pull/9403
			saashq.throw(
				_("Please check the filter values set for Dashboard Chart: {}").format(
					get_link_to_form(chart.doctype, chart.name)
				),
				title=_("Invalid Filter Value"),
			)
			return
		else:
			raise

	if not saashq.flags.read_only:
		saashq.db.set_value(
			"Dashboard Chart", args.chart_name, "last_synced_on", saashq.utils.now(), update_modified=False
		)
	return results


def get_dashboards_with_link(docname, doctype):
	links = []

	if doctype == "Dashboard Chart":
		links = saashq.get_all("Dashboard Chart Link", fields=["parent"], filters={"chart": docname})
	elif doctype == "Number Card":
		links = saashq.get_all("Number Card Link", fields=["parent"], filters={"card": docname})

	return [link.parent for link in links]


def sync_dashboards(app=None):
	"""Import, overwrite dashboards from `[app]/[app]_dashboard`"""
	apps = [app] if app else saashq.get_installed_apps()

	for app_name in apps:
		print(f"Updating Dashboard for {app_name}")
		for module_name in saashq.local.app_modules.get(app_name) or []:
			saashq.flags.in_import = True
			make_records_in_module(app_name, module_name)
			saashq.flags.in_import = False


def make_records_in_module(app, module):
	dashboards_path = saashq.get_module_path(module, f"{module}_dashboard")
	charts_path = saashq.get_module_path(module, "dashboard chart")
	cards_path = saashq.get_module_path(module, "number card")

	paths = [dashboards_path, charts_path, cards_path]
	for path in paths:
		make_records(path)


def make_records(path, filters=None):
	if os.path.isdir(path):
		for fname in os.listdir(path):
			if os.path.isdir(join(path, fname)):
				if fname == "__pycache__":
					continue
				import_file_by_path(f"{path}/{fname}/{fname}.json")
