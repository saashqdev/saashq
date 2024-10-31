import saashq
from saashq.model.utils.rename_field import rename_field


def execute():
	if not saashq.db.table_exists("Dashboard Chart"):
		return

	saashq.reload_doc("desk", "doctype", "dashboard_chart")

	if saashq.db.has_column("Dashboard Chart", "is_custom"):
		rename_field("Dashboard Chart", "is_custom", "use_report_chart")
