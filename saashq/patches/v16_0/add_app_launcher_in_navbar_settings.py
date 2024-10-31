# Copyright (c) 2023, SaasHQ
# MIT License. See license.txt

import saashq


def execute():
	if saashq.db.exists("Navbar Item", {"item_label": "Apps"}):
		return

	navbar_settings = saashq.get_single("Navbar Settings")
	settings_items = navbar_settings.as_dict().settings_dropdown

	view_website_item_idx = -1
	for i, item in enumerate(navbar_settings.settings_dropdown):
		if item.get("item_label") == "View Website":
			view_website_item_idx = i

	settings_items.insert(
		view_website_item_idx + 1,
		{
			"item_label": "Apps",
			"item_type": "Route",
			"route": "/apps",
			"is_standard": 1,
		},
	)

	navbar_settings.set("settings_dropdown", settings_items)
	navbar_settings.save()