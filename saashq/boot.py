# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE
"""
bootstrap client session
"""

import os

import saashq
import saashq.defaults
import saashq.desk.desk_page
from saashq.core.doctype.navbar_settings.navbar_settings import get_app_logo, get_navbar_settings
from saashq.desk.doctype.changelog_feed.changelog_feed import get_changelog_feed_items
from saashq.desk.doctype.form_tour.form_tour import get_onboarding_ui_tours
from saashq.desk.doctype.route_history.route_history import frequently_visited_links
from saashq.desk.form.load import get_meta_bundle
from saashq.email.inbox import get_email_accounts
from saashq.model.base_document import get_controller
from saashq.permissions import has_permission
from saashq.query_builder import DocType
from saashq.query_builder.functions import Count
from saashq.query_builder.terms import ParameterizedValueWrapper, SubQuery
from saashq.social.doctype.energy_point_log.energy_point_log import get_energy_points
from saashq.social.doctype.energy_point_settings.energy_point_settings import (
	is_energy_point_enabled,
)
from saashq.utils import add_user_info, cstr, get_system_timezone
from saashq.utils.change_log import get_versions
from saashq.utils.saashqcloud import on_saashqcloud
from saashq.website.doctype.web_page_view.web_page_view import is_tracking_enabled


def get_bootinfo():
	"""build and return boot info"""
	from saashq.translate import get_lang_dict, get_translated_doctypes

	saashq.set_user_lang(saashq.session.user)
	bootinfo = saashq._dict()
	hooks = saashq.get_hooks()
	doclist = []

	# user
	get_user(bootinfo)

	# system info
	bootinfo.sitename = saashq.local.site
	bootinfo.sysdefaults = saashq.defaults.get_defaults()
	bootinfo.server_date = saashq.utils.nowdate()

	if saashq.session["user"] != "Guest":
		bootinfo.user_info = get_user_info()

	bootinfo.modules = {}
	bootinfo.module_list = []
	load_desktop_data(bootinfo)
	bootinfo.letter_heads = get_letter_heads()
	bootinfo.active_domains = saashq.get_active_domains()
	bootinfo.all_domains = [d.get("name") for d in saashq.get_all("Domain")]
	add_layouts(bootinfo)

	bootinfo.module_app = saashq.local.module_app
	bootinfo.single_types = [d.name for d in saashq.get_all("DocType", {"issingle": 1})]
	bootinfo.nested_set_doctypes = [
		d.parent for d in saashq.get_all("DocField", {"fieldname": "lft"}, ["parent"])
	]
	add_home_page(bootinfo, doclist)
	bootinfo.page_info = get_allowed_pages()
	load_translations(bootinfo)
	add_timezone_info(bootinfo)
	load_conf_settings(bootinfo)
	load_print(bootinfo, doclist)
	doclist.extend(get_meta_bundle("Page"))
	bootinfo.home_folder = saashq.db.get_value("File", {"is_home_folder": 1})
	bootinfo.navbar_settings = get_navbar_settings()
	bootinfo.notification_settings = get_notification_settings()
	bootinfo.onboarding_tours = get_onboarding_ui_tours()
	set_time_zone(bootinfo)

	# ipinfo
	if saashq.session.data.get("ipinfo"):
		bootinfo.ipinfo = saashq.session["data"]["ipinfo"]

	# add docs
	bootinfo.docs = doclist
	load_country_doc(bootinfo)
	load_currency_docs(bootinfo)

	for method in hooks.boot_session or []:
		saashq.get_attr(method)(bootinfo)

	if bootinfo.lang:
		bootinfo.lang = str(bootinfo.lang)
	bootinfo.versions = {k: v["version"] for k, v in get_versions().items()}

	bootinfo.error_report_email = saashq.conf.error_report_email
	bootinfo.calendars = sorted(saashq.get_hooks("calendars"))
	bootinfo.treeviews = saashq.get_hooks("treeviews") or []
	bootinfo.lang_dict = get_lang_dict()
	bootinfo.success_action = get_success_action()
	bootinfo.update(get_email_accounts(user=saashq.session.user))
	bootinfo.energy_points_enabled = is_energy_point_enabled()
	bootinfo.website_tracking_enabled = is_tracking_enabled()
	bootinfo.points = get_energy_points(saashq.session.user)
	bootinfo.frequently_visited_links = frequently_visited_links()
	bootinfo.link_preview_doctypes = get_link_preview_doctypes()
	bootinfo.additional_filters_config = get_additional_filters_from_hooks()
	bootinfo.desk_settings = get_desk_settings()
	bootinfo.app_logo_url = get_app_logo()
	bootinfo.link_title_doctypes = get_link_title_doctypes()
	bootinfo.translated_doctypes = get_translated_doctypes()
	bootinfo.subscription_conf = add_subscription_conf()
	bootinfo.marketplace_apps = get_marketplace_apps()
	bootinfo.changelog_feed = get_changelog_feed_items()
	bootinfo.enable_address_autocompletion = saashq.db.get_single_value(
		"Geolocation Settings", "enable_address_autocompletion"
	)

	if sentry_dsn := get_sentry_dsn():
		bootinfo.sentry_dsn = sentry_dsn

	return bootinfo


def get_letter_heads():
	letter_heads = {}

	if not saashq.has_permission("Letter Head"):
		return letter_heads
	for letter_head in saashq.get_list("Letter Head", fields=["name", "content", "footer"]):
		letter_heads.setdefault(
			letter_head.name, {"header": letter_head.content, "footer": letter_head.footer}
		)

	return letter_heads


def load_conf_settings(bootinfo):
	from saashq.core.api.file import get_max_file_size

	bootinfo.max_file_size = get_max_file_size()
	for key in ("developer_mode", "socketio_port", "file_watcher_port"):
		if key in saashq.conf:
			bootinfo[key] = saashq.conf.get(key)


def load_desktop_data(bootinfo):
	from saashq.desk.desktop import get_workspace_sidebar_items

	bootinfo.sidebar_pages = get_workspace_sidebar_items()
	allowed_pages = [d.name for d in bootinfo.sidebar_pages.get("pages")]
	bootinfo.module_wise_workspaces = get_controller("Workspace").get_module_wise_workspaces()
	bootinfo.dashboards = saashq.get_all("Dashboard")
	bootinfo.app_data = []

	Workspace = saashq.qb.DocType("Workspace")
	Module = saashq.qb.DocType("Module Def")

	for app_name in saashq.get_installed_apps():
		# get app details from app_info (/apps)
		apps = saashq.get_hooks("add_to_apps_screen", app_name=app_name)
		app_info = {}
		if apps:
			app_info = apps[0]
			has_permission = app_info.get("has_permission")
			if has_permission and not saashq.get_attr(has_permission)():
				continue

		workspaces = [
			r[0]
			for r in (
				saashq.qb.from_(Workspace)
				.inner_join(Module)
				.on(Workspace.module == Module.name)
				.select(Workspace.name)
				.where(Module.app_name == app_name)
				.run()
			)
			if r[0] in allowed_pages
		]

		bootinfo.app_data.append(
			dict(
				app_name=app_info.get("name") or app_name,
				app_title=app_info.get("title")
				or (
					saashq.get_hooks("app_title", app_name=app_name)
					and saashq.get_hooks("app_title", app_name=app_name)[0]
					or ""
				)
				or app_name,
				app_route=(
					saashq.get_hooks("app_home", app_name=app_name)
					and saashq.get_hooks("app_home", app_name=app_name)[0]
				)
				or (workspaces and "/app/" + saashq.utils.slug(workspaces[0]))
				or "",
				app_logo_url=app_info.get("logo")
				or saashq.get_hooks("app_logo_url", app_name=app_name)
				or saashq.get_hooks("app_logo_url", app_name="saashq"),
				modules=[m.name for m in saashq.get_all("Module Def", dict(app_name=app_name))],
				workspaces=workspaces,
			)
		)


def get_allowed_pages(cache=False):
	return get_user_pages_or_reports("Page", cache=cache)


def get_allowed_reports(cache=False):
	return get_user_pages_or_reports("Report", cache=cache)


def get_allowed_report_names(cache=False) -> set[str]:
	return {cstr(report) for report in get_allowed_reports(cache).keys() if report}


def get_user_pages_or_reports(parent, cache=False):
	if cache:
		has_role = saashq.cache.get_value("has_role:" + parent, user=saashq.session.user)
		if has_role:
			return has_role

	roles = saashq.get_roles()
	has_role = {}

	page = DocType("Page")
	report = DocType("Report")

	is_report = parent == "Report"

	if is_report:
		columns = (report.name.as_("title"), report.ref_doctype, report.report_type)
	else:
		columns = (page.title.as_("title"),)

	customRole = DocType("Custom Role")
	hasRole = DocType("Has Role")
	parentTable = DocType(parent)

	# get pages or reports set on custom role
	pages_with_custom_roles = (
		saashq.qb.from_(customRole)
		.from_(hasRole)
		.from_(parentTable)
		.select(customRole[parent.lower()].as_("name"), customRole.modified, customRole.ref_doctype, *columns)
		.where(
			(hasRole.parent == customRole.name)
			& (parentTable.name == customRole[parent.lower()])
			& (customRole[parent.lower()].isnotnull())
			& (hasRole.role.isin(roles))
		)
	).run(as_dict=True)

	for p in pages_with_custom_roles:
		has_role[p.name] = {"modified": p.modified, "title": p.title, "ref_doctype": p.ref_doctype}

	subq = (
		saashq.qb.from_(customRole)
		.select(customRole[parent.lower()])
		.where(customRole[parent.lower()].isnotnull())
	)

	pages_with_standard_roles = (
		saashq.qb.from_(hasRole)
		.from_(parentTable)
		.select(parentTable.name.as_("name"), parentTable.modified, *columns)
		.where(
			(hasRole.role.isin(roles)) & (hasRole.parent == parentTable.name) & (parentTable.name.notin(subq))
		)
		.distinct()
	)

	if is_report:
		pages_with_standard_roles = pages_with_standard_roles.where(report.disabled == 0)

	pages_with_standard_roles = pages_with_standard_roles.run(as_dict=True)

	for p in pages_with_standard_roles:
		if p.name not in has_role:
			has_role[p.name] = {"modified": p.modified, "title": p.title}
			if parent == "Report":
				has_role[p.name].update({"ref_doctype": p.ref_doctype})

	no_of_roles = SubQuery(
		saashq.qb.from_(hasRole).select(Count("*")).where(hasRole.parent == parentTable.name)
	)

	# pages and reports with no role are allowed
	rows_with_no_roles = (
		saashq.qb.from_(parentTable)
		.select(parentTable.name, parentTable.modified, *columns)
		.where(no_of_roles == 0)
	).run(as_dict=True)

	for r in rows_with_no_roles:
		if r.name not in has_role:
			has_role[r.name] = {"modified": r.modified, "title": r.title}
			if is_report:
				has_role[r.name] |= {"ref_doctype": r.ref_doctype}

	if is_report:
		if not has_permission("Report", print_logs=False):
			return {}

		reports = saashq.get_list(
			"Report",
			fields=["name", "report_type"],
			filters={"name": ("in", has_role.keys())},
			ignore_ifnull=True,
		)
		for report in reports:
			has_role[report.name]["report_type"] = report.report_type

		non_permitted_reports = set(has_role.keys()) - {r.name for r in reports}
		for r in non_permitted_reports:
			has_role.pop(r, None)

	# Expire every six hours
	saashq.cache.set_value("has_role:" + parent, has_role, saashq.session.user, 21600)
	return has_role


def load_translations(bootinfo):
	from saashq.translate import get_messages_for_boot

	bootinfo["lang"] = saashq.lang
	bootinfo["__messages"] = get_messages_for_boot()


def get_user_info():
	# get info for current user
	user_info = saashq._dict()
	add_user_info(saashq.session.user, user_info)

	return user_info


def get_user(bootinfo):
	"""get user info"""
	bootinfo.user = saashq.get_user().load_user()


def add_home_page(bootinfo, docs):
	"""load home page"""
	if saashq.session.user == "Guest":
		return
	home_page = saashq.db.get_default("desktop:home_page")

	if home_page == "setup-wizard":
		bootinfo.setup_wizard_requires = saashq.get_hooks("setup_wizard_requires")

	try:
		page = saashq.desk.desk_page.get(home_page)
		docs.append(page)
		bootinfo["home_page"] = page.name
	except (saashq.DoesNotExistError, saashq.PermissionError):
		saashq.clear_last_message()
		bootinfo["home_page"] = "Workspaces"


def add_timezone_info(bootinfo):
	system = bootinfo.sysdefaults.get("time_zone")
	import saashq.utils.momentjs

	bootinfo.timezone_info = {"zones": {}, "rules": {}, "links": {}}
	saashq.utils.momentjs.update(system, bootinfo.timezone_info)


def load_print(bootinfo, doclist):
	print_settings = saashq.db.get_singles_dict("Print Settings")
	print_settings.doctype = ":Print Settings"
	doclist.append(print_settings)
	load_print_css(bootinfo, print_settings)


def load_print_css(bootinfo, print_settings):
	import saashq.www.printview

	bootinfo.print_css = saashq.www.printview.get_print_style(
		print_settings.print_style or "Redesign", for_legacy=True
	)


def get_unseen_notes():
	note = DocType("Note")
	nsb = DocType("Note Seen By").as_("nsb")

	return (
		saashq.qb.from_(note)
		.select(note.name, note.title, note.content, note.notify_on_every_login)
		.where(
			(note.notify_on_login == 1)
			& (note.expire_notification_on > saashq.utils.now())
			& (
				ParameterizedValueWrapper(saashq.session.user).notin(
					SubQuery(saashq.qb.from_(nsb).select(nsb.user).where(nsb.parent == note.name))
				)
			)
		)
	).run(as_dict=1)


def get_success_action():
	return saashq.get_all("Success Action", fields=["*"])


def get_link_preview_doctypes():
	from saashq.utils import cint

	link_preview_doctypes = [d.name for d in saashq.get_all("DocType", {"show_preview_popup": 1})]
	customizations = saashq.get_all(
		"Property Setter", fields=["doc_type", "value"], filters={"property": "show_preview_popup"}
	)

	for custom in customizations:
		if not cint(custom.value) and custom.doc_type in link_preview_doctypes:
			link_preview_doctypes.remove(custom.doc_type)
		else:
			link_preview_doctypes.append(custom.doc_type)

	return link_preview_doctypes


def get_additional_filters_from_hooks():
	filter_config = saashq._dict()
	filter_hooks = saashq.get_hooks("filters_config")
	for hook in filter_hooks:
		filter_config.update(saashq.get_attr(hook)())

	return filter_config


def add_layouts(bootinfo):
	# add routes for readable doctypes
	bootinfo.doctype_layouts = saashq.get_all("DocType Layout", ["name", "route", "document_type"])


def get_desk_settings():
	from saashq.core.doctype.user.user import desk_properties

	return saashq.get_value("User", saashq.session.user, desk_properties, as_dict=True)


def get_notification_settings():
	return saashq.get_cached_doc("Notification Settings", saashq.session.user)


def get_link_title_doctypes():
	dts = saashq.get_all("DocType", {"show_title_field_in_link": 1})
	custom_dts = saashq.get_all(
		"Property Setter",
		{"property": "show_title_field_in_link", "value": "1"},
		["doc_type as name"],
	)
	return [d.name for d in dts + custom_dts if d]


def set_time_zone(bootinfo):
	bootinfo.time_zone = {
		"system": get_system_timezone(),
		"user": bootinfo.get("user_info", {}).get(saashq.session.user, {}).get("time_zone", None)
		or get_system_timezone(),
	}


def load_country_doc(bootinfo):
	country = saashq.db.get_default("country")
	if not country:
		return
	try:
		bootinfo.docs.append(saashq.get_cached_doc("Country", country))
	except Exception:
		pass


def load_currency_docs(bootinfo):
	currency = saashq.qb.DocType("Currency")

	currency_docs = (
		saashq.qb.from_(currency)
		.select(
			currency.name,
			currency.fraction,
			currency.fraction_units,
			currency.number_format,
			currency.smallest_currency_fraction_value,
			currency.symbol,
			currency.symbol_on_right,
		)
		.where(currency.enabled == 1)
		.run(as_dict=1, update={"doctype": ":Currency"})
	)

	bootinfo.docs += currency_docs


def get_marketplace_apps():
	import requests

	apps = []
	cache_key = "saashq_marketplace_apps"

	if saashq.conf.developer_mode or not on_saashqcloud():
		return apps

	def get_apps_from_fc():
		remote_site = saashq.conf.saashqcloud_url or "saashqcloud.com"
		request_url = f"https://{remote_site}/api/method/press.api.marketplace.get_marketplace_apps"
		request = requests.get(request_url, timeout=2.0)
		return request.json()["message"]

	try:
		apps = saashq.cache.get_value(cache_key, get_apps_from_fc, shared=True)
		installed_apps = set(saashq.get_installed_apps())
		apps = [app for app in apps if app["name"] not in installed_apps]
	except Exception:
		# Don't retry for a day
		saashq.cache.set_value(cache_key, apps, shared=True, expires_in_sec=24 * 60 * 60)

	return apps


def add_subscription_conf():
	try:
		return saashq.conf.subscription
	except Exception:
		return ""


def get_sentry_dsn():
	if not saashq.get_system_settings("enable_telemetry"):
		return

	return os.getenv("SAASHQ_SENTRY_DSN")
