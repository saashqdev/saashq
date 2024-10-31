# Copyright (c) 2023, SaasHQ
# MIT License. See license.txt

import saashq
from saashq.core.doctype.user.user import desk_properties


def execute():
	roles = {role.name: role for role in saashq.get_all("Role", fields=["*"])}

	for user in saashq.get_list("User"):
		user_desk_settings = {}
		for role_name in saashq.get_roles(username=user.name):
			if role := roles.get(role_name):
				for key in desk_properties:
					if role.get(key) is None:
						role[key] = 1
					user_desk_settings[key] = user_desk_settings.get(key) or role.get(key)

		saashq.db.set_value("User", user.name, user_desk_settings)
