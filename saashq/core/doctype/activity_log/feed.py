# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq
import saashq.permissions
from saashq import _
from saashq.core.doctype.activity_log.activity_log import add_authentication_log
from saashq.utils import get_fullname


def login_feed(login_manager):
	if login_manager.user != "Guest":
		subject = _("{0} logged in").format(get_fullname(login_manager.user))
		add_authentication_log(subject, login_manager.user)


def logout_feed(user, reason):
	if user and user != "Guest":
		subject = _("{0} logged out: {1}").format(get_fullname(user), saashq.bold(reason))
		add_authentication_log(subject, user, operation="Logout")
