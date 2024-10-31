# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE
import getpass

import saashq
from saashq.geo.doctype.country.country import import_country_and_currency
from saashq.utils import cint
from saashq.utils.password import update_password


def before_install():
	saashq.reload_doc("core", "doctype", "doctype_state")
	saashq.reload_doc("core", "doctype", "docfield")
	saashq.reload_doc("core", "doctype", "docperm")
	saashq.reload_doc("core", "doctype", "doctype_action")
	saashq.reload_doc("core", "doctype", "doctype_link")
	saashq.reload_doc("desk", "doctype", "form_tour_step")
	saashq.reload_doc("desk", "doctype", "form_tour")
	saashq.reload_doc("core", "doctype", "doctype")
	saashq.clear_cache()


def after_install():
	create_user_type()
	install_basic_docs()

	from saashq.core.doctype.file.utils import make_home_folder
	from saashq.core.doctype.language.language import sync_languages

	make_home_folder()
	import_country_and_currency()
	sync_languages()

	# save default print setting
	print_settings = saashq.get_doc("Print Settings")
	print_settings.save()

	# all roles to admin
	saashq.get_doc("User", "Administrator").add_roles(*saashq.get_all("Role", pluck="name"))

	# update admin password
	update_password("Administrator", get_admin_password())

	if not saashq.conf.skip_setup_wizard:
		# only set home_page if the value doesn't exist in the db
		if not saashq.db.get_default("desktop:home_page"):
			saashq.db.set_default("desktop:home_page", "setup-wizard")
			saashq.db.set_single_value("System Settings", "setup_complete", 0)

	# clear test log
	from saashq.tests.utils.generators import _after_install_clear_test_log

	_after_install_clear_test_log()

	add_standard_navbar_items()

	saashq.db.commit()


def create_user_type():
	for user_type in ["System User", "Website User"]:
		if not saashq.db.exists("User Type", user_type):
			saashq.get_doc({"doctype": "User Type", "name": user_type, "is_standard": 1}).insert(
				ignore_permissions=True
			)


def install_basic_docs():
	# core users / roles
	install_docs = [
		{
			"doctype": "User",
			"name": "Administrator",
			"first_name": "Administrator",
			"email": "admin@example.com",
			"enabled": 1,
			"is_admin": 1,
			"roles": [{"role": "Administrator"}],
			"thread_notify": 0,
			"send_me_a_copy": 0,
		},
		{
			"doctype": "User",
			"name": "Guest",
			"first_name": "Guest",
			"email": "guest@example.com",
			"enabled": 1,
			"is_guest": 1,
			"roles": [{"role": "Guest"}],
			"thread_notify": 0,
			"send_me_a_copy": 0,
		},
		{"doctype": "Role", "role_name": "Report Manager"},
		{"doctype": "Role", "role_name": "Translator"},
		{
			"doctype": "Workflow State",
			"workflow_state_name": "Pending",
			"icon": "question-sign",
			"style": "",
		},
		{
			"doctype": "Workflow State",
			"workflow_state_name": "Approved",
			"icon": "ok-sign",
			"style": "Success",
		},
		{
			"doctype": "Workflow State",
			"workflow_state_name": "Rejected",
			"icon": "remove",
			"style": "Danger",
		},
		{"doctype": "Workflow Action Master", "workflow_action_name": "Approve"},
		{"doctype": "Workflow Action Master", "workflow_action_name": "Reject"},
		{"doctype": "Workflow Action Master", "workflow_action_name": "Review"},
		{
			"doctype": "Email Domain",
			"domain_name": "example.com",
			"email_id": "account@example.com",
			"password": "pass",
			"email_server": "imap.example.com",
			"use_imap": 1,
			"smtp_server": "smtp.example.com",
		},
		{
			"doctype": "Email Account",
			"domain": "example.com",
			"email_id": "notifications@example.com",
			"default_outgoing": 1,
		},
		{
			"doctype": "Email Account",
			"domain": "example.com",
			"email_id": "replies@example.com",
			"default_incoming": 1,
		},
	]

	for d in install_docs:
		try:
			saashq.get_doc(d).insert(ignore_if_duplicate=True)
		except saashq.NameError:
			pass


def get_admin_password():
	return saashq.conf.get("admin_password") or getpass.getpass("Set Administrator password: ")


def before_tests():
	if len(saashq.get_installed_apps()) > 1:
		# don't run before tests if any other app is installed
		return

	saashq.db.truncate("Custom Field")
	saashq.db.truncate("Event")

	saashq.clear_cache()

	# complete setup if missing
	if not cint(saashq.db.get_single_value("System Settings", "setup_complete")):
		complete_setup_wizard()

	saashq.db.set_single_value("Website Settings", "disable_signup", 0)
	saashq.db.commit()
	saashq.clear_cache()


def complete_setup_wizard():
	from saashq.desk.page.setup_wizard.setup_wizard import setup_complete

	setup_complete(
		{
			"language": "English",
			"email": "test@erpnexus.com",
			"full_name": "Test User",
			"password": "test",
			"country": "United States",
			"timezone": "America/New_York",
			"currency": "USD",
			"enable_telemtry": 1,
		}
	)


def add_standard_navbar_items():
	navbar_settings = saashq.get_single("Navbar Settings")

	# don't add settings/help options if they're already present
	if navbar_settings.settings_dropdown and navbar_settings.help_dropdown:
		return

	navbar_settings.settings_dropdown = []
	navbar_settings.help_dropdown = []

	for item in saashq.get_hooks("standard_navbar_items"):
		navbar_settings.append("settings_dropdown", item)

	for item in saashq.get_hooks("standard_help_items"):
		navbar_settings.append("help_dropdown", item)

	navbar_settings.save()
