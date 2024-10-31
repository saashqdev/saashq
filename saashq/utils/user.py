# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

from email.utils import formataddr
from typing import TYPE_CHECKING

import saashq
import saashq.share
from saashq import _dict
from saashq.boot import get_allowed_reports
from saashq.core.doctype.domain_settings.domain_settings import get_active_modules
from saashq.permissions import AUTOMATIC_ROLES, get_roles, get_valid_perms
from saashq.query_builder import DocType, Order
from saashq.query_builder.functions import Concat_ws

if TYPE_CHECKING:
	from saashq.core.doctype.user.user import User


class UserPermissions:
	"""
	A user permission object can be accessed as `saashq.get_user()`
	"""

	def __init__(self, name=""):
		self.defaults = None
		self.name = name or saashq.session.get("user")
		self.roles = []

		self.all_read = []
		self.can_create = []
		self.can_select = []
		self.can_read = []
		self.can_write = []
		self.can_submit = []
		self.can_cancel = []
		self.can_delete = []
		self.can_search = []
		self.can_get_report = []
		self.can_import = []
		self.can_export = []
		self.can_print = []
		self.can_email = []
		self.allow_modules = []
		self.in_create = []
		self.setup_user()

	def setup_user(self):
		def get_user_doc():
			user = None
			try:
				user = saashq.get_doc("User", self.name).as_dict()
			except saashq.DoesNotExistError:
				pass
			except Exception as e:
				# install boo-boo
				if not saashq.db.is_table_missing(e):
					raise

			return user

		if not saashq.flags.in_install_db and not saashq.flags.in_test:
			user_doc = saashq.cache.hget("user_doc", self.name, get_user_doc)
			if user_doc:
				self.doc = saashq.get_doc(user_doc)

	def get_roles(self):
		"""get list of roles"""
		if not self.roles:
			self.roles = get_roles(self.name)
		return self.roles

	def build_doctype_map(self):
		"""build map of special doctype properties"""
		self.doctype_map = {}

		active_domains = saashq.get_active_domains()
		all_doctypes = saashq.get_all(
			"DocType",
			fields=[
				"name",
				"in_create",
				"module",
				"istable",
				"issingle",
				"read_only",
				"restrict_to_domain",
			],
		)

		for dt in all_doctypes:
			if not dt.restrict_to_domain or (dt.restrict_to_domain in active_domains):
				self.doctype_map[dt["name"]] = dt

	def build_perm_map(self):
		"""build map of permissions at level 0"""
		self.perm_map = {}
		for r in get_valid_perms():
			dt = r["parent"]

			if dt not in self.perm_map:
				self.perm_map[dt] = {}

			for k in saashq.permissions.rights:
				if not self.perm_map[dt].get(k):
					self.perm_map[dt][k] = r.get(k)

	def build_permissions(self):
		"""build lists of what the user can read / write / create
		quirks:
		        read_only => Not in Search
		        in_create => Not in create
		"""
		self.build_doctype_map()
		self.build_perm_map()
		user_shared = saashq.share.get_shared_doctypes()
		no_list_view_link = []
		active_modules = get_active_modules() or []
		for dt in self.doctype_map:
			dtp = self.doctype_map[dt]

			p = self.perm_map.get(dt, {})

			if not p.get("read") and (dt in user_shared):
				p["read"] = 1

			if p.get("select"):
				self.can_select.append(dt)

			if not dtp.get("istable"):
				if p.get("create") and not dtp.get("issingle"):
					if dtp.get("in_create"):
						self.in_create.append(dt)
					else:
						self.can_create.append(dt)
				elif p.get("write"):
					self.can_write.append(dt)
				elif p.get("read"):
					if dtp.get("read_only"):
						# read_only = "User Cannot Search"
						self.all_read.append(dt)
						no_list_view_link.append(dt)
					else:
						self.can_read.append(dt)

			if p.get("submit"):
				self.can_submit.append(dt)

			if p.get("cancel"):
				self.can_cancel.append(dt)

			if p.get("delete"):
				self.can_delete.append(dt)

			if p.get("read") or p.get("write") or p.get("create"):
				if p.get("report"):
					self.can_get_report.append(dt)
				for key in ("import", "export", "print", "email"):
					if p.get(key):
						getattr(self, "can_" + key).append(dt)

				if not dtp.get("istable"):
					if not dtp.get("issingle") and not dtp.get("read_only"):
						self.can_search.append(dt)
					if dtp.get("module") not in self.allow_modules:
						if active_modules and dtp.get("module") not in active_modules:
							pass
						else:
							self.allow_modules.append(dtp.get("module"))

		self.can_write += self.can_create
		self.can_write += self.in_create
		self.can_read += self.can_write

		self.shared = saashq.get_all(
			"DocShare", {"user": self.name, "read": 1}, distinct=True, pluck="share_doctype"
		)
		self.can_read = list(set(self.can_read + self.shared))
		self.all_read += self.can_read

		for dt in no_list_view_link:
			if dt in self.can_read:
				self.can_read.remove(dt)

		if "System Manager" in self.get_roles():
			self.can_import += saashq.get_all("DocType", {"allow_import": 1}, pluck="name")
			self.can_import += saashq.get_all(
				"Property Setter",
				pluck="doc_type",
				filters={"property": "allow_import", "value": "1"},
			)

		saashq.cache.hset("can_import", saashq.session.user, self.can_import)

	def get_defaults(self):
		import saashq.defaults

		self.defaults = saashq.defaults.get_defaults(self.name)
		return self.defaults

	def _get(self, key):
		if not self.can_read:
			self.build_permissions()
		return getattr(self, key)

	def get_can_read(self):
		"""return list of doctypes that the user can read"""
		if not self.can_read:
			self.build_permissions()
		return self.can_read

	def load_user(self):
		d = saashq.db.get_value(
			"User",
			self.name,
			[
				"creation",
				"desk_theme",
				"code_editor_type",
				"document_follow_notify",
				"email",
				"email_signature",
				"first_name",
				"language",
				"last_name",
				"mute_sounds",
				"send_me_a_copy",
				"user_type",
				"onboarding_status",
				"default_workspace",
			],
			as_dict=True,
		)

		if not self.can_read:
			self.build_permissions()

		if d.get("default_workspace"):
			workspace = saashq.get_cached_doc("Workspace", d.default_workspace)
			d.default_workspace = {
				"name": workspace.name,
				"public": workspace.public,
				"title": workspace.title,
			}

		d.name = self.name
		d.onboarding_status = saashq.parse_json(d.onboarding_status)
		d.roles = self.get_roles()
		d.defaults = self.get_defaults()
		for key in (
			"can_select",
			"can_create",
			"can_write",
			"can_read",
			"can_submit",
			"can_cancel",
			"can_delete",
			"can_get_report",
			"allow_modules",
			"all_read",
			"can_search",
			"in_create",
			"can_export",
			"can_import",
			"can_print",
			"can_email",
		):
			d[key] = list(set(getattr(self, key)))

		d.all_reports = self.get_all_reports()
		return d

	def get_all_reports(self):
		return get_allowed_reports()


def get_user_fullname(user: str) -> str:
	user_doctype = DocType("User")
	return (
		saashq.get_value(
			user_doctype,
			filters={"name": user},
			fieldname=Concat_ws(" ", user_doctype.first_name, user_doctype.last_name),
		)
		or ""
	)


def get_fullname_and_avatar(user: str) -> _dict:
	first_name, last_name, avatar, name = saashq.db.get_value(
		"User", user, ["first_name", "last_name", "user_image", "name"], order_by=None
	)
	return _dict(
		{
			"fullname": " ".join(list(filter(None, [first_name, last_name]))),
			"avatar": avatar,
			"name": name,
		}
	)


def get_system_managers(only_name: bool = False) -> list[str]:
	"""Return all system manager's user details."""
	HasRole = DocType("Has Role")
	User = DocType("User")

	if only_name:
		fields = [User.name]
	else:
		fields = [User.full_name, User.name]

	system_managers = (
		saashq.qb.from_(User)
		.join(HasRole)
		.on(HasRole.parent == User.name)
		.where(
			(HasRole.parenttype == "User")
			& (User.enabled == 1)
			& (HasRole.role == "System Manager")
			& (User.docstatus < 2)
			& (User.name.notin(saashq.STANDARD_USERS))
		)
		.select(*fields)
		.orderby(User.creation, order=Order.desc)
		.run(as_dict=True)
	)

	if only_name:
		return [p.name for p in system_managers]
	else:
		return [formataddr((p.full_name, p.name)) for p in system_managers]


def add_role(user: str, role: str) -> None:
	saashq.get_doc("User", user).add_roles(role)


def add_system_manager(
	email: str,
	first_name: str | None = None,
	last_name: str | None = None,
	send_welcome_email: bool = False,
	password: str | None = None,
) -> "User":
	# add user
	user = saashq.new_doc("User")
	user.update(
		{
			"name": email,
			"email": email,
			"enabled": 1,
			"first_name": first_name or email,
			"last_name": last_name,
			"user_type": "System User",
			"send_welcome_email": 1 if send_welcome_email else 0,
		}
	)

	user.insert()

	# add roles
	roles = saashq.get_all(
		"Role",
		fields=["name"],
		filters={"name": ["not in", AUTOMATIC_ROLES]},
	)
	roles = [role.name for role in roles]
	user.add_roles(*roles)

	if password:
		from saashq.utils.password import update_password

		update_password(user=user.name, pwd=password)
	return user


def get_enabled_system_users() -> list[dict]:
	return saashq.get_all(
		"User",
		fields=["email", "language", "name"],
		filters={
			"user_type": "System User",
			"enabled": 1,
			"name": ["not in", ("Administrator", "Guest")],
		},
	)


def is_website_user(username: str | None = None) -> str | None:
	return saashq.db.get_value("User", username or saashq.session.user, "user_type") == "Website User"


def is_system_user(username: str | None = None) -> str | None:
	# TODO: Depracate this. Inefficient, incorrect. This function is meant to be used in emails only.
	# Problem: Filters on email instead of PK, implicitly filters out disabled users.
	return saashq.db.get_value(
		"User",
		{
			"email": username or saashq.session.user,
			"enabled": 1,
			"user_type": "System User",
		},
		cache=True,
	)


def get_users() -> list[dict]:
	from saashq.core.doctype.user.user import get_system_users

	system_managers = get_system_managers(only_name=True)

	return [
		{
			"full_name": get_user_fullname(user),
			"email": user,
			"is_system_manager": user in system_managers,
		}
		for user in get_system_users()
	]


def get_users_with_role(role: str) -> list[str]:
	User = DocType("User")
	HasRole = DocType("Has Role")

	return (
		saashq.qb.from_(HasRole)
		.from_(User)
		.where(
			(HasRole.role == role)
			& (User.name != "Administrator")
			& (User.enabled == 1)
			& (HasRole.parent == User.name)
		)
		.select(User.name)
		.distinct()
		.run(pluck=True)
	)
