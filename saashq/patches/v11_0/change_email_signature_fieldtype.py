# Copyright (c) 2018, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import saashq


def execute():
	signatures = saashq.db.get_list("User", {"email_signature": ["!=", ""]}, ["name", "email_signature"])
	saashq.reload_doc("core", "doctype", "user")
	for d in signatures:
		signature = d.get("email_signature")
		signature = signature.replace("\n", "<br>")
		signature = "<div>" + signature + "</div>"
		saashq.db.set_value("User", d.get("name"), "email_signature", signature)
