# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq


def execute():
	saashq.reload_doc("website", "doctype", "website_theme_ignore_app")
	themes = saashq.get_all("Website Theme", filters={"theme_url": ("not like", "/files/website_theme/%")})
	for theme in themes:
		doc = saashq.get_doc("Website Theme", theme.name)
		try:
			doc.save()
		except Exception:
			print("Ignoring....")
			print(saashq.get_traceback())
