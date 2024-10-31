import saashq


def execute():
	navbar_settings = saashq.get_single("Navbar Settings")

	if saashq.db.exists("Navbar Item", {"item_label": "Toggle Theme"}):
		return

	for navbar_item in navbar_settings.settings_dropdown[6:]:
		navbar_item.idx = navbar_item.idx + 1

	navbar_settings.append(
		"settings_dropdown",
		{
			"item_label": "Toggle Theme",
			"item_type": "Action",
			"action": "new saashq.ui.ThemeSwitcher().show()",
			"is_standard": 1,
			"idx": 7,
		},
	)

	navbar_settings.save()
