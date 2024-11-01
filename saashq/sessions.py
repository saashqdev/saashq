# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE
"""
Boot session from cache or build

Session bootstraps info needed by common client side activities including
permission, homepage, default variables, system defaults etc
"""
import json
from urllib.parse import unquote

import redis

import saashq
import saashq.defaults
import saashq.model.meta
import saashq.translate
import saashq.utils
from saashq import _
from saashq.apps import get_apps, get_default_path, is_desk_apps
from saashq.cache_manager import clear_user_cache
from saashq.query_builder import Order
from saashq.utils import cint, cstr, get_assets_json
from saashq.utils.change_log import has_app_update_notifications
from saashq.utils.data import add_to_date


@saashq.whitelist()
def clear():
	saashq.local.session_obj.update(force=True)
	saashq.local.db.commit()
	clear_user_cache(saashq.session.user)
	saashq.response["message"] = _("Cache Cleared")


def clear_sessions(user=None, keep_current=False, force=False):
	"""Clear other sessions of the current user. Called at login / logout

	:param user: user name (default: current user)
	:param keep_current: keep current session (default: false)
	:param force: triggered by the user (default false)
	"""

	reason = "Logged In From Another Session"
	if force:
		reason = "Force Logged out by the user"

	for sid in get_sessions_to_clear(user, keep_current, force):
		delete_session(sid, reason=reason)


def get_sessions_to_clear(user=None, keep_current=False, force=False):
	"""Return sessions of the current user. Called at login / logout.

	:param user: user name (default: current user)
	:param keep_current: keep current session (default: false)
	:param force: ignore simultaneous sessions count, log the user out of all except current (default: false)
	"""
	if not user:
		user = saashq.session.user

	offset = 0
	if not force and user == saashq.session.user:
		simultaneous_sessions = saashq.db.get_value("User", user, "simultaneous_sessions") or 1
		offset = simultaneous_sessions

	session = saashq.qb.DocType("Sessions")
	session_id = saashq.qb.from_(session).where(session.user == user)
	if keep_current:
		if not force:
			offset = max(0, offset - 1)
		session_id = session_id.where(session.sid != saashq.session.sid)

	query = (
		session_id.select(session.sid).offset(offset).limit(100).orderby(session.lastupdate, order=Order.desc)
	)

	return query.run(pluck=True)


def delete_session(sid=None, user=None, reason="Session Expired"):
	from saashq.core.doctype.activity_log.feed import logout_feed

	if saashq.flags.read_only:
		# This isn't manually initiated logout, most likely user's cookies were expired in such case
		# we should just ignore it till database is back up again.
		return

	if sid and not user:
		table = saashq.qb.DocType("Sessions")
		user_details = saashq.qb.from_(table).where(table.sid == sid).select(table.user).run(as_dict=True)
		if user_details:
			user = user_details[0].get("user")

	logout_feed(user, reason)
	saashq.db.delete("Sessions", {"sid": sid})
	saashq.db.commit()

	saashq.cache.hdel("session", sid)
	saashq.cache.hdel("last_db_session_update", sid)


def clear_all_sessions(reason=None):
	"""This effectively logs out all users"""
	saashq.only_for("Administrator")
	if not reason:
		reason = "Deleted All Active Session"
	for sid in saashq.qb.from_("Sessions").select("sid").run(pluck=True):
		delete_session(sid, reason=reason)


def get_expired_sessions():
	"""Return list of expired sessions."""

	sessions = saashq.qb.DocType("Sessions")
	return (
		saashq.qb.from_(sessions).select(sessions.sid).where(sessions.lastupdate < get_expired_threshold())
	).run(pluck=True)


def clear_expired_sessions():
	"""This function is meant to be called from scheduler"""
	for sid in get_expired_sessions():
		delete_session(sid, reason="Session Expired")


def get():
	"""get session boot info"""
	from saashq.boot import get_bootinfo, get_unseen_notes
	from saashq.utils.change_log import get_change_log

	bootinfo = None
	if not getattr(saashq.conf, "disable_session_cache", None):
		# check if cache exists
		bootinfo = saashq.cache.hget("bootinfo", saashq.session.user)
		if bootinfo:
			bootinfo["from_cache"] = 1
			bootinfo["user"]["recent"] = json.dumps(saashq.cache.hget("user_recent", saashq.session.user))

	if not bootinfo:
		# if not create it
		bootinfo = get_bootinfo()
		saashq.cache.hset("bootinfo", saashq.session.user, bootinfo)
		try:
			saashq.cache.ping()
		except redis.exceptions.ConnectionError:
			message = _("Redis cache server not running. Please contact Administrator / Tech support")
			if "messages" in bootinfo:
				bootinfo["messages"].append(message)
			else:
				bootinfo["messages"] = [message]

		# check only when clear cache is done, and don't cache this
		if saashq.local.request:
			bootinfo["change_log"] = get_change_log()

	bootinfo["metadata_version"] = saashq.cache.get_value("metadata_version")
	if not bootinfo["metadata_version"]:
		bootinfo["metadata_version"] = saashq.reset_metadata_version()

	bootinfo.notes = get_unseen_notes()
	bootinfo.assets_json = get_assets_json()
	bootinfo.read_only = bool(saashq.flags.read_only)

	for hook in saashq.get_hooks("extend_bootinfo"):
		saashq.get_attr(hook)(bootinfo=bootinfo)

	bootinfo["lang"] = saashq.translate.get_user_lang()
	bootinfo["disable_async"] = saashq.conf.disable_async

	bootinfo["setup_complete"] = cint(saashq.get_system_settings("setup_complete"))
	bootinfo["apps_data"] = {
		"apps": get_apps() or [],
		"is_desk_apps": 1 if bool(is_desk_apps(get_apps())) else 0,
		"default_path": get_default_path() or "",
	}

	bootinfo["desk_theme"] = saashq.db.get_value("User", saashq.session.user, "desk_theme") or "Light"
	bootinfo["user"]["impersonated_by"] = saashq.session.data.get("impersonated_by")
	bootinfo["navbar_settings"] = saashq.get_cached_doc("Navbar Settings")
	bootinfo.has_app_updates = has_app_update_notifications()

	return bootinfo


@saashq.whitelist()
def get_boot_assets_json():
	return get_assets_json()


def get_csrf_token():
	if not saashq.local.session.data.csrf_token:
		generate_csrf_token()

	return saashq.local.session.data.csrf_token


def generate_csrf_token():
	saashq.local.session.data.csrf_token = saashq.generate_hash()
	if not saashq.flags.in_test:
		saashq.local.session_obj.update(force=True)


class Session:
	__slots__ = ("user", "user_type", "full_name", "data", "time_diff", "sid", "_update_in_cache")

	def __init__(self, user, resume=False, full_name=None, user_type=None):
		self.sid = cstr(saashq.form_dict.get("sid") or unquote(saashq.request.cookies.get("sid", "Guest")))
		self.user = user
		self.user_type = user_type
		self.full_name = full_name
		self.data = saashq._dict({"data": saashq._dict({})})
		self.time_diff = None
		self._update_in_cache = False

		# set local session
		saashq.local.session = self.data

		if resume:
			self.resume()

		else:
			if self.user:
				self.validate_user()
				self.start()

	def validate_user(self):
		if not saashq.get_cached_value("User", self.user, "enabled"):
			saashq.throw(
				_("User {0} is disabled. Please contact your System Manager.").format(self.user),
				saashq.ValidationError,
			)

	def start(self):
		"""start a new session"""
		# generate sid
		if self.user == "Guest":
			sid = "Guest"
		else:
			sid = saashq.generate_hash()

		self.data.user = self.user
		self.sid = self.data.sid = sid
		self.data.data.user = self.user
		self.data.data.session_ip = saashq.local.request_ip
		if self.user != "Guest":
			self.data.data.update(
				{
					"last_updated": saashq.utils.now(),
					"session_expiry": get_expiry_period(),
					"full_name": self.full_name,
					"user_type": self.user_type,
				}
			)

		# insert session
		if self.user != "Guest":
			self.insert_session_record()

			# update user
			user = saashq.get_doc("User", self.data["user"])
			user_doctype = saashq.qb.DocType("User")
			(
				saashq.qb.update(user_doctype)
				.set(user_doctype.last_login, saashq.utils.now())
				.set(user_doctype.last_ip, saashq.local.request_ip)
				.set(user_doctype.last_active, saashq.utils.now())
				.where(user_doctype.name == self.data["user"])
			).run()

			user.run_notifications("before_change")
			user.run_notifications("on_update")
			saashq.db.commit()

	def insert_session_record(self):
		Sessions = saashq.qb.DocType("Sessions")
		now = saashq.utils.now()

		(
			saashq.qb.into(Sessions)
			.columns(Sessions.sessiondata, Sessions.user, Sessions.lastupdate, Sessions.sid, Sessions.status)
			.insert(
				(
					saashq.as_json(self.data["data"], indent=None, separators=(",", ":")),
					self.data["user"],
					now,
					self.data["sid"],
					"Active",
				)
			)
		).run()
		saashq.cache.hset("session", self.data.sid, self.data)

	def resume(self):
		"""non-login request: load a session"""
		import saashq
		from saashq.auth import validate_ip_address

		data = self.get_session_record()

		if data:
			self.data.update({"data": data, "user": data.user, "sid": self.sid})
			self.user = data.user
			self.validate_user()
			validate_ip_address(self.user)
		else:
			self.start_as_guest()

		if self.sid != "Guest":
			saashq.local.user_lang = saashq.translate.get_user_lang(self.data.user)
			saashq.local.lang = saashq.local.user_lang

	def get_session_record(self):
		"""get session record, or return the standard Guest Record"""
		from saashq.auth import clear_cookies

		r = self.get_session_data()

		if not r:
			saashq.response["session_expired"] = 1
			clear_cookies()
			self.sid = "Guest"
			r = self.get_session_data()

		return r

	def get_session_data(self):
		if self.sid == "Guest":
			return saashq._dict({"user": "Guest"})

		data = self.get_session_data_from_cache()
		if not data:
			self._update_in_cache = True
			data = self.get_session_data_from_db()
		return data

	def get_session_data_from_cache(self):
		data = saashq.cache.hget("session", self.sid)
		if data:
			data = saashq._dict(data)
			session_data = data.get("data", {})

			# set user for correct timezone
			self.time_diff = saashq.utils.time_diff_in_seconds(
				saashq.utils.now(), session_data.get("last_updated")
			)
			expiry = get_expiry_in_seconds(session_data.get("session_expiry"))

			if self.time_diff > expiry:
				self._delete_session()
				data = None

		return data and data.data

	def get_session_data_from_db(self):
		sessions = saashq.qb.DocType("Sessions")

		record = (
			saashq.qb.from_(sessions)
			.select(sessions.user, sessions.sessiondata)
			.where(sessions.sid == self.sid)
			.where(sessions.lastupdate > get_expired_threshold())
		).run()

		if record:
			data = saashq.parse_json(record[0][1] or "{}")
			data.user = record[0][0]
		else:
			self._delete_session()
			data = None

		return data

	def _delete_session(self):
		delete_session(self.sid, reason="Session Expired")

	def start_as_guest(self):
		"""all guests share the same 'Guest' session"""
		self.user = "Guest"
		self.start()

	def update(self, force=False):
		"""extend session expiry"""

		if saashq.session.user == "Guest":
			return

		now = saashq.utils.now()

		Sessions = saashq.qb.DocType("Sessions")

		# update session in db
		last_updated = saashq.cache.hget("last_db_session_update", self.sid)
		time_diff = saashq.utils.time_diff_in_seconds(now, last_updated) if last_updated else None

		# database persistence is secondary, don't update it too often
		updated_in_db = False
		if (force or (time_diff is None) or (time_diff > 600)) and not saashq.flags.read_only:
			self.data.data.last_updated = now
			self.data.data.lang = str(saashq.lang)
			# update sessions table
			(
				saashq.qb.update(Sessions)
				.where(Sessions.sid == self.data["sid"])
				.set(
					Sessions.sessiondata,
					saashq.as_json(self.data["data"], indent=None, separators=(",", ":")),
				)
				.set(Sessions.lastupdate, now)
			).run()

			saashq.db.set_value("User", saashq.session.user, "last_active", now, update_modified=False)

			saashq.db.commit()
			updated_in_db = True

			saashq.cache.hset("last_db_session_update", self.sid, now)
			saashq.cache.hset("session", self.sid, self.data)

		return updated_in_db

	def set_impersonsated(self, original_user):
		self.data.data.impersonated_by = original_user
		# Forcefully flush session
		self.update(force=True)


def get_expiry_period_for_query():
	if saashq.db.db_type == "postgres":
		return get_expiry_period()
	else:
		return get_expiry_in_seconds()


def get_expiry_in_seconds(expiry=None):
	if not expiry:
		expiry = get_expiry_period()

	parts = expiry.split(":")
	return (cint(parts[0]) * 3600) + (cint(parts[1]) * 60) + cint(parts[2])


def get_expired_threshold():
	"""Get cutoff time before which all sessions are considered expired."""

	now = saashq.utils.now()
	expiry_in_seconds = get_expiry_in_seconds()

	return add_to_date(now, seconds=-expiry_in_seconds, as_string=True)


def get_expiry_period():
	exp_sec = saashq.defaults.get_global_default("session_expiry") or "240:00:00"

	# incase seconds is missing
	if len(exp_sec.split(":")) == 2:
		exp_sec = exp_sec + ":00"

	return exp_sec


def get_geo_from_ip(ip_addr):
	try:
		from geolite2 import geolite2

		with geolite2 as f:
			reader = f.reader()
			data = reader.get(ip_addr)

			return saashq._dict(data)
	except ImportError:
		return
	except ValueError:
		return
	except TypeError:
		return


def get_geo_ip_country(ip_addr):
	match = get_geo_from_ip(ip_addr)
	if match:
		return match.country
