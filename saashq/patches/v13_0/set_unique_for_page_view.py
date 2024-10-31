import saashq


def execute():
	saashq.reload_doc("website", "doctype", "web_page_view", force=True)
	site_url = saashq.utils.get_site_url(saashq.local.site)
	saashq.db.sql(f"""UPDATE `tabWeb Page View` set is_unique=1 where referrer LIKE '%{site_url}%'""")
