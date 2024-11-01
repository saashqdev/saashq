# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq
import saashq.www.list
from saashq import _

no_cache = 1


def get_context(context):
	if saashq.session.user == "Guest":
		saashq.throw(_("You need to be logged in to access this page"), saashq.PermissionError)

	context.current_user = saashq.get_doc("User", saashq.session.user)
	context.show_sidebar = False
