import saashq


def execute():
	saashq.reload_doc("core", "doctype", "domain")
	saashq.reload_doc("core", "doctype", "has_domain")
	active_domains = saashq.get_active_domains()
	all_domains = saashq.get_all("Domain")

	for d in all_domains:
		if d.name not in active_domains:
			inactive_domain = saashq.get_doc("Domain", d.name)
			inactive_domain.setup_data()
			inactive_domain.remove_custom_field()
