import saashq
from saashq.model.naming import append_number_if_name_exists
from saashq.utils.dashboard import get_dashboards_with_link


def execute():
	if (
		not saashq.db.table_exists("Dashboard Chart")
		or not saashq.db.table_exists("Number Card")
		or not saashq.db.table_exists("Dashboard")
	):
		return

	saashq.reload_doc("desk", "doctype", "dashboard_chart")
	saashq.reload_doc("desk", "doctype", "number_card")
	saashq.reload_doc("desk", "doctype", "dashboard")

	modified_charts = get_modified_docs("Dashboard Chart")
	modified_cards = get_modified_docs("Number Card")
	modified_dashboards = [doc.name for doc in get_modified_docs("Dashboard")]

	for chart in modified_charts:
		modified_dashboards += get_dashboards_with_link(chart.name, "Dashboard Chart")
		rename_modified_doc(chart.name, "Dashboard Chart")

	for card in modified_cards:
		modified_dashboards += get_dashboards_with_link(card.name, "Number Card")
		rename_modified_doc(card.name, "Number Card")

	modified_dashboards = list(set(modified_dashboards))

	for dashboard in modified_dashboards:
		rename_modified_doc(dashboard, "Dashboard")


def get_modified_docs(doctype):
	return saashq.get_all(doctype, filters={"owner": "Administrator", "modified_by": ["!=", "Administrator"]})


def rename_modified_doc(docname, doctype):
	new_name = docname + " Custom"
	try:
		saashq.rename_doc(doctype, docname, new_name)
	except saashq.ValidationError:
		new_name = append_number_if_name_exists(doctype, new_name)
		saashq.rename_doc(doctype, docname, new_name)
