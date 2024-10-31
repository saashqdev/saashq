import saashq


def execute():
	saashq.reload_doc("website", "doctype", "web_page_view", force=True)
	saashq.db.sql("""UPDATE `tabWeb Page View` set path='/' where path=''""")
