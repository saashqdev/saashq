import saashq
import saashq.www.list
from saashq import _

no_cache = 1


def get_context(context):
	if saashq.session.user == "Guest":
		saashq.throw(_("You need to be logged in to access this page"), saashq.PermissionError)

	active_tokens = saashq.get_all(
		"OAuth Bearer Token",
		filters=[["user", "=", saashq.session.user]],
		fields=["client"],
		distinct=True,
		order_by="creation",
	)

	client_apps = []

	for token in active_tokens:
		creation = get_first_login(token.client)
		app = {
			"name": token.get("client"),
			"app_name": saashq.db.get_value("OAuth Client", token.get("client"), "app_name"),
			"creation": creation,
		}
		client_apps.append(app)

	app = None
	if "app" in saashq.form_dict:
		app = saashq.get_doc("OAuth Client", saashq.form_dict.app)
		app = app.__dict__
		app["client_secret"] = None

	if app:
		context.app = app

	context.apps = client_apps


def get_first_login(client):
	login_date = saashq.get_all(
		"OAuth Bearer Token",
		filters=[["user", "=", saashq.session.user], ["client", "=", client]],
		fields=["creation"],
		order_by="creation",
		limit=1,
	)

	login_date = login_date[0].get("creation") if login_date and len(login_date) > 0 else None

	return login_date


@saashq.whitelist()
def delete_client(client_id: str):
	active_client_id_tokens = saashq.get_all(
		"OAuth Bearer Token", filters=[["user", "=", saashq.session.user], ["client", "=", client_id]]
	)
	for token in active_client_id_tokens:
		saashq.delete_doc("OAuth Bearer Token", token.get("name"), ignore_permissions=True)
