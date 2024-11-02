# Copyright (c) 2019, Saashq Technologies and contributors
# License: MIT. See LICENSE

import datetime

import pytz

import saashq
from saashq import _
from saashq.model.document import Document
from saashq.utils import cint, cstr, get_system_timezone


class TokenCache(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.integrations.doctype.oauth_scope.oauth_scope import OAuthScope
		from saashq.types import DF

		access_token: DF.Password | None
		connected_app: DF.Link | None
		expires_in: DF.Int
		provider_name: DF.Data | None
		refresh_token: DF.Password | None
		scopes: DF.Table[OAuthScope]
		state: DF.Data | None
		success_uri: DF.Data | None
		token_type: DF.Data | None
		user: DF.Link | None
	# end: auto-generated types

	def get_auth_header(self):
		if self.access_token:
			return {"Authorization": "Bearer " + self.get_password("access_token")}
		raise saashq.exceptions.DoesNotExistError

	def update_data(self, data):
		"""
		Store data returned by authorization flow.

		Params:
		data - Dict with access_token, refresh_token, expires_in and scope.
		"""
		token_type = cstr(data.get("token_type", "")).lower()
		if token_type not in ["bearer", "mac"]:
			saashq.throw(_("Received an invalid token type."))
		# 'Bearer' or 'MAC'
		token_type = token_type.title() if token_type == "bearer" else token_type.upper()

		self.token_type = token_type
		self.access_token = cstr(data.get("access_token", ""))
		self.expires_in = cint(data.get("expires_in", 0))

		if "refresh_token" in data:
			self.refresh_token = cstr(data.get("refresh_token"))

		new_scopes = data.get("scope")
		if new_scopes:
			if isinstance(new_scopes, str):
				new_scopes = new_scopes.split(" ")
			if isinstance(new_scopes, list):
				self.scopes = None
				for scope in new_scopes:
					self.append("scopes", {"scope": scope})

		self.state = None
		self.save(ignore_permissions=True)
		saashq.db.commit()
		return self

	def get_expires_in(self):
		system_timezone = pytz.timezone(get_system_timezone())
		modified = saashq.utils.get_datetime(self.modified)
		modified = system_timezone.localize(modified)
		expiry_utc = modified.astimezone(pytz.utc) + datetime.timedelta(seconds=self.expires_in)
		now_utc = datetime.datetime.now(pytz.utc)
		return cint((expiry_utc - now_utc).total_seconds())

	def is_expired(self):
		return self.get_expires_in() < 0

	def get_json(self):
		return {
			"access_token": self.get_password("access_token", False),
			"refresh_token": self.get_password("refresh_token", False),
			"expires_in": self.get_expires_in(),
			"token_type": self.token_type,
		}
