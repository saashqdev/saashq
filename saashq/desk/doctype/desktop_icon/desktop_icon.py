# Copyright (c) 2015, Saashq Technologies Pvt. Ltd. and contributors
# License: MIT. See LICENSE

import json
import random

import saashq
from saashq import _
from saashq.model.document import Document
from saashq.utils.user import UserPermissions


class DesktopIcon(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		_doctype: DF.Link | None
		_report: DF.Link | None
		app: DF.Data | None
		blocked: DF.Check
		category: DF.Data | None
		color: DF.Data | None
		custom: DF.Check
		description: DF.SmallText | None
		force_show: DF.Check
		hidden: DF.Check
		icon: DF.Data | None
		idx: DF.Int
		label: DF.Data | None
		link: DF.SmallText | None
		module_name: DF.Data | None
		reverse: DF.Check
		standard: DF.Check
		type: DF.Literal["module", "list", "link", "page", "query-report"]
	# end: auto-generated types

	def validate(self):
		if not self.label:
			self.label = self.module_name

	def on_trash(self):
		clear_desktop_icons_cache()


def after_doctype_insert():
	saashq.db.add_unique("Desktop Icon", ("module_name", "owner", "standard"))


def get_desktop_icons(user=None):
	"""Return desktop icons for user"""
	if not user:
		user = saashq.session.user

	user_icons = saashq.cache.hget("desktop_icons", user)

	if not user_icons:
		fields = [
			"module_name",
			"hidden",
			"label",
			"link",
			"type",
			"icon",
			"color",
			"description",
			"category",
			"_doctype",
			"_report",
			"idx",
			"force_show",
			"reverse",
			"custom",
			"standard",
			"blocked",
		]

		active_domains = saashq.get_active_domains()

		blocked_doctypes = saashq.get_all(
			"DocType",
			filters={"ifnull(restrict_to_domain, '')": ("not in", ",".join(active_domains))},
			fields=["name"],
		)

		blocked_doctypes = [d.get("name") for d in blocked_doctypes]

		standard_icons = saashq.get_all("Desktop Icon", fields=fields, filters={"standard": 1})

		standard_map = {}
		for icon in standard_icons:
			if icon._doctype in blocked_doctypes:
				icon.blocked = 1
			standard_map[icon.module_name] = icon

		user_icons = saashq.get_all("Desktop Icon", fields=fields, filters={"standard": 0, "owner": user})

		# update hidden property
		for icon in user_icons:
			standard_icon = standard_map.get(icon.module_name, None)

			if icon._doctype in blocked_doctypes:
				icon.blocked = 1

			# override properties from standard icon
			if standard_icon:
				for key in ("route", "label", "color", "icon", "link"):
					if standard_icon.get(key):
						icon[key] = standard_icon.get(key)

				if standard_icon.blocked:
					icon.hidden = 1

					# flag for modules_select dialog
					icon.hidden_in_standard = 1

				elif standard_icon.force_show:
					icon.hidden = 0

		# add missing standard icons (added via new install apps?)
		user_icon_names = [icon.module_name for icon in user_icons]
		for standard_icon in standard_icons:
			if standard_icon.module_name not in user_icon_names:
				# if blocked, hidden too!
				if standard_icon.blocked:
					standard_icon.hidden = 1
					standard_icon.hidden_in_standard = 1

				user_icons.append(standard_icon)

		user_blocked_modules = saashq.get_doc("User", user).get_blocked_modules()
		for icon in user_icons:
			if icon.module_name in user_blocked_modules:
				icon.hidden = 1

		# sort by idx
		user_icons.sort(key=lambda a: a.idx)

		# translate
		for d in user_icons:
			if d.label:
				d.label = _(d.label, context=d.parent)

		saashq.cache.hset("desktop_icons", user, user_icons)

	return user_icons


@saashq.whitelist()
def add_user_icon(_doctype, _report=None, label=None, link=None, type="link", standard=0):
	"""Add a new user desktop icon to the desktop"""

	if not label:
		label = _doctype or _report
	if not link:
		link = f"List/{_doctype}"

	# find if a standard icon exists
	icon_name = saashq.db.exists(
		"Desktop Icon", {"standard": standard, "link": link, "owner": saashq.session.user}
	)

	if icon_name:
		if saashq.db.get_value("Desktop Icon", icon_name, "hidden"):
			# if it is hidden, unhide it
			saashq.db.set_value("Desktop Icon", icon_name, "hidden", 0)
			clear_desktop_icons_cache()

	else:
		idx = (
			saashq.db.sql("select max(idx) from `tabDesktop Icon` where owner=%s", saashq.session.user)[0][0]
			or saashq.db.sql("select count(*) from `tabDesktop Icon` where standard=1")[0][0]
		)

		if not saashq.db.get_value("Report", _report):
			_report = None
			userdefined_icon = saashq.db.get_value(
				"DocType", _doctype, ["icon", "color", "module"], as_dict=True
			)
		else:
			userdefined_icon = saashq.db.get_value(
				"Report", _report, ["icon", "color", "module"], as_dict=True
			)

		module_icon = saashq.get_value(
			"Desktop Icon",
			{"standard": 1, "module_name": userdefined_icon.module},
			["name", "icon", "color", "reverse"],
			as_dict=True,
		)

		if not module_icon:
			module_icon = saashq._dict()
			opts = random.choice(palette)
			module_icon.color = opts[0]
			module_icon.reverse = 0 if (len(opts) > 1) else 1

		try:
			new_icon = saashq.get_doc(
				{
					"doctype": "Desktop Icon",
					"label": label,
					"module_name": label,
					"link": link,
					"type": type,
					"_doctype": _doctype,
					"_report": _report,
					"icon": userdefined_icon.icon or module_icon.icon,
					"color": userdefined_icon.color or module_icon.color,
					"reverse": module_icon.reverse,
					"idx": idx + 1,
					"custom": 1,
					"standard": standard,
				}
			).insert(ignore_permissions=True)
			clear_desktop_icons_cache()

			icon_name = new_icon.name

		except saashq.UniqueValidationError:
			saashq.throw(_("Desktop Icon already exists"))
		except Exception as e:
			raise e

	return icon_name


@saashq.whitelist()
def set_order(new_order, user=None):
	"""set new order by duplicating user icons (if user is set) or set global order"""
	if isinstance(new_order, str):
		new_order = json.loads(new_order)
	for i, module_name in enumerate(new_order):
		if module_name not in ("Explore",):
			if user:
				icon = get_user_copy(module_name, user)
			else:
				name = saashq.db.get_value("Desktop Icon", {"standard": 1, "module_name": module_name})
				if name:
					icon = saashq.get_doc("Desktop Icon", name)
				else:
					# standard icon missing, create one for DocType
					name = add_user_icon(module_name, standard=1)
					icon = saashq.get_doc("Desktop Icon", name)

			icon.db_set("idx", i)

	clear_desktop_icons_cache()


def set_desktop_icons(visible_list, ignore_duplicate=True):
	"""Resets all lists and makes only the given one standard,
	if the desktop icon does not exist and the name is a DocType, then will create
	an icon for the doctype"""

	# clear all custom only if setup is not complete
	if not saashq.defaults.get_defaults().get("setup_complete", 0):
		saashq.db.delete("Desktop Icon", {"standard": 0})

	# set standard as blocked and hidden if setting first active domain
	if not saashq.flags.keep_desktop_icons:
		saashq.db.sql("update `tabDesktop Icon` set blocked=0, hidden=1 where standard=1")

	# set as visible if present, or add icon
	for module_name in list(visible_list):
		name = saashq.db.get_value("Desktop Icon", {"module_name": module_name})
		if name:
			saashq.db.set_value("Desktop Icon", name, "hidden", 0)
		else:
			if saashq.db.exists("DocType", module_name):
				try:
					add_user_icon(module_name, standard=1)
				except saashq.UniqueValidationError as e:
					if not ignore_duplicate:
						raise e
					else:
						visible_list.remove(module_name)
						saashq.clear_last_message()

	# set the order
	set_order(visible_list)

	clear_desktop_icons_cache()


def set_hidden_list(hidden_list, user=None):
	"""Sets property `hidden`=1 in **Desktop Icon** for given user.
	If user is None then it will set global values.
	It will also set the rest of the icons as shown (`hidden` = 0)"""
	if isinstance(hidden_list, str):
		hidden_list = json.loads(hidden_list)

	# set as hidden
	for module_name in hidden_list:
		set_hidden(module_name, user, 1)

	# set as seen
	for module_name in list(set(get_all_icons()) - set(hidden_list)):
		set_hidden(module_name, user, 0)

	if user:
		clear_desktop_icons_cache()
	else:
		saashq.clear_cache()


def set_hidden(module_name, user=None, hidden=1):
	"""Set module hidden property for given user. If user is not specified,
	hide/unhide it globally"""
	if user:
		icon = get_user_copy(module_name, user)

		if hidden and icon.custom:
			saashq.delete_doc(icon.doctype, icon.name, ignore_permissions=True)
			return

		# hidden by user
		icon.db_set("hidden", hidden)
	else:
		icon = saashq.get_doc("Desktop Icon", {"standard": 1, "module_name": module_name})

		# blocked is globally hidden
		icon.db_set("blocked", hidden)


def get_all_icons():
	return [
		d.module_name for d in saashq.get_all("Desktop Icon", filters={"standard": 1}, fields=["module_name"])
	]


def clear_desktop_icons_cache(user=None):
	saashq.cache.hdel("desktop_icons", user or saashq.session.user)
	saashq.cache.hdel("bootinfo", user or saashq.session.user)


def get_user_copy(module_name, user=None):
	"""Return user copy (Desktop Icon) of the given module_name. If user copy does not exist, create one.

	:param module_name: Name of the module
	:param user: User for which the copy is required (optional)
	"""
	if not user:
		user = saashq.session.user

	desktop_icon_name = saashq.db.get_value(
		"Desktop Icon", {"module_name": module_name, "owner": user, "standard": 0}
	)

	if desktop_icon_name:
		return saashq.get_doc("Desktop Icon", desktop_icon_name)
	else:
		return make_user_copy(module_name, user)


def make_user_copy(module_name, user):
	"""Insert and return the user copy of a standard Desktop Icon"""
	standard_name = saashq.db.get_value("Desktop Icon", {"module_name": module_name, "standard": 1})

	if not standard_name:
		saashq.throw(_("{0} not found").format(module_name), saashq.DoesNotExistError)

	original = saashq.get_doc("Desktop Icon", standard_name)

	desktop_icon = saashq.get_doc(
		{"doctype": "Desktop Icon", "standard": 0, "owner": user, "module_name": module_name}
	)

	for key in (
		"app",
		"label",
		"route",
		"type",
		"_doctype",
		"idx",
		"reverse",
		"force_show",
		"link",
		"icon",
		"color",
	):
		if original.get(key):
			desktop_icon.set(key, original.get(key))

	desktop_icon.insert(ignore_permissions=True)

	return desktop_icon


def sync_desktop_icons():
	"""Sync desktop icons from all apps"""
	for app in saashq.get_installed_apps():
		sync_from_app(app)


def sync_from_app(app):
	"""Sync desktop icons from app. To be called during install"""
	try:
		modules = saashq.get_attr(app + ".config.desktop.get_data")() or {}
	except ImportError:
		return []

	if isinstance(modules, dict):
		modules_list = []
		for m, desktop_icon in modules.items():
			desktop_icon["module_name"] = m
			modules_list.append(desktop_icon)
	else:
		modules_list = modules

	for i, m in enumerate(modules_list):
		desktop_icon_name = saashq.db.get_value(
			"Desktop Icon", {"module_name": m["module_name"], "app": app, "standard": 1}
		)
		if desktop_icon_name:
			desktop_icon = saashq.get_doc("Desktop Icon", desktop_icon_name)
		else:
			# new icon
			desktop_icon = saashq.get_doc(
				{"doctype": "Desktop Icon", "idx": i, "standard": 1, "app": app, "owner": "Administrator"}
			)

		if "doctype" in m:
			m["_doctype"] = m.pop("doctype")

		desktop_icon.update(m)
		try:
			desktop_icon.save()
		except saashq.exceptions.UniqueValidationError:
			pass

	return modules_list


@saashq.whitelist()
def update_icons(hidden_list, user=None):
	"""update modules"""
	if not user:
		saashq.only_for("System Manager")

	set_hidden_list(hidden_list, user)
	saashq.msgprint(saashq._("Updated"), indicator="green", title=_("Success"), alert=True)


def get_context(context):
	context.icons = get_user_icons(saashq.session.user)
	context.user = saashq.session.user

	if "System Manager" in saashq.get_roles():
		context.users = saashq.get_all(
			"User",
			filters={"user_type": "System User", "enabled": 1},
			fields=["name", "first_name", "last_name"],
		)


@saashq.whitelist()
def get_module_icons(user=None):
	if user != saashq.session.user:
		saashq.only_for("System Manager")

	if not user:
		icons = saashq.get_all("Desktop Icon", fields="*", filters={"standard": 1}, order_by="idx")
	else:
		saashq.cache.hdel("desktop_icons", user)
		icons = get_user_icons(user)

	for icon in icons:
		icon.value = saashq.db.escape(_(icon.label or icon.module_name))

	return {"icons": icons, "user": user}


def get_user_icons(user):
	"""Get user icons for module setup page"""
	user_perms = UserPermissions(user)
	user_perms.build_permissions()

	from saashq.boot import get_allowed_pages

	allowed_pages = get_allowed_pages()

	icons = []
	for icon in get_desktop_icons(user):
		add = True
		if icon.hidden_in_standard:
			add = False

		if not icon.custom:
			if icon.module_name == ["Help", "Settings"]:
				pass

			elif icon.type == "page" and icon.link not in allowed_pages:
				add = False

			elif icon.type == "module" and icon.module_name not in user_perms.allow_modules:
				add = False

		if add:
			icons.append(icon)

	return icons


palette = (
	("#FFC4C4",),
	("#FFE8CD",),
	("#FFD2C2",),
	("#FF8989",),
	("#FFD19C",),
	("#FFA685",),
	("#FF4D4D", 1),
	("#FFB868",),
	("#FF7846", 1),
	("#A83333", 1),
	("#A87945", 1),
	("#A84F2E", 1),
	("#D2D2FF",),
	("#F8D4F8",),
	("#DAC7FF",),
	("#A3A3FF",),
	("#F3AAF0",),
	("#B592FF",),
	("#7575FF", 1),
	("#EC7DEA", 1),
	("#8E58FF", 1),
	("#4D4DA8", 1),
	("#934F92", 1),
	("#5E3AA8", 1),
	("#EBF8CC",),
	("#FFD7D7",),
	("#D2F8ED",),
	("#D9F399",),
	("#FFB1B1",),
	("#A4F3DD",),
	("#C5EC63",),
	("#FF8989", 1),
	("#77ECCA",),
	("#7B933D", 1),
	("#A85B5B", 1),
	("#49937E", 1),
	("#FFFACD",),
	("#D2F1FF",),
	("#CEF6D1",),
	("#FFF69C",),
	("#A6E4FF",),
	("#9DECA2",),
	("#FFF168",),
	("#78D6FF",),
	("#6BE273",),
	("#A89F45", 1),
	("#4F8EA8", 1),
	("#428B46", 1),
)


@saashq.whitelist()
def hide(name, user=None):
	if not user:
		user = saashq.session.user

	try:
		set_hidden(name, user, hidden=1)
		clear_desktop_icons_cache()
	except Exception:
		return False

	return True
