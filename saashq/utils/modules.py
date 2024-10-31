import saashq
from saashq import _


def get_modules_from_all_apps_for_user(user: str | None = None) -> list[dict]:
	user = user or saashq.session.user
	all_modules = get_modules_from_all_apps()
	global_blocked_modules = saashq.get_doc("User", "Administrator").get_blocked_modules()
	user_blocked_modules = saashq.get_doc("User", user).get_blocked_modules()
	blocked_modules = global_blocked_modules + user_blocked_modules
	allowed_modules_list = [m for m in all_modules if m.get("module_name") not in blocked_modules]

	empty_tables_by_module = get_all_empty_tables_by_module()

	for module in allowed_modules_list:
		module_name = module.get("module_name")

		# Apply onboarding status
		if module_name in empty_tables_by_module:
			module["onboard_present"] = 1

	return allowed_modules_list


def get_modules_from_all_apps():
	modules_list = []
	for app in saashq.get_installed_apps():
		modules_list += get_modules_from_app(app)
	return modules_list


def get_modules_from_app(app):
	return saashq.get_all("Module Def", filters={"app_name": app}, fields=["module_name", "app_name as app"])


def get_all_empty_tables_by_module():
	table_rows = saashq.qb.Field("table_rows")
	table_name = saashq.qb.Field("table_name")
	information_schema = saashq.qb.Schema("information_schema")

	empty_tables = (
		saashq.qb.from_(information_schema.tables).select(table_name).where(table_rows == 0)
	).run()

	empty_tables = {r[0] for r in empty_tables}

	results = saashq.get_all("DocType", fields=["name", "module"])
	empty_tables_by_module = {}

	for doctype, module in results:
		if f"tab{doctype}" in empty_tables:
			if module in empty_tables_by_module:
				empty_tables_by_module[module].append(doctype)
			else:
				empty_tables_by_module[module] = [doctype]
	return empty_tables_by_module


def is_domain(module):
	return module.get("category") == "Domains"


def is_module(module):
	return module.get("type") == "module"
