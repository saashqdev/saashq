import saashq

base_template_path = "www/robots.txt"


def get_context(context):
	robots_txt = (
		saashq.db.get_single_value("Website Settings", "robots_txt")
		or (saashq.local.conf.robots_txt and saashq.read_file(saashq.local.conf.robots_txt))
		or ""
	)

	return {"robots_txt": robots_txt}
