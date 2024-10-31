import json

import saashq
from saashq.client import set_value


def get_email_accounts(user=None):
	if not user:
		user = saashq.session.user

	email_accounts = []

	accounts = saashq.get_all(
		"User Email",
		filters={"parent": user},
		fields=["email_account", "email_id", "enable_outgoing"],
		distinct=True,
		order_by="idx",
	)

	if not accounts:
		return {"email_accounts": [], "all_accounts": ""}

	all_accounts = ",".join(account.get("email_account") for account in accounts)
	if len(accounts) > 1:
		email_accounts.append({"email_account": all_accounts, "email_id": "All Accounts"})
	email_accounts.extend(accounts)

	email_accounts.extend(
		[
			{"email_account": "Sent", "email_id": "Sent Mail"},
			{"email_account": "Spam", "email_id": "Spam"},
			{"email_account": "Trash", "email_id": "Trash"},
		]
	)

	return {"email_accounts": email_accounts, "all_accounts": all_accounts}


@saashq.whitelist()
def create_email_flag_queue(names, action):
	"""create email flag queue to mark email either as read or unread"""

	def mark_as_seen_unseen(name, action):
		doc = saashq.get_doc("Communication", name)
		if action == "Read":
			doc.add_seen()
		else:
			_seen = json.loads(doc._seen or "[]")
			_seen = [user for user in _seen if saashq.session.user != user]
			doc.db_set("_seen", json.dumps(_seen), update_modified=False)

	if not all([names, action]):
		return

	for name in json.loads(names or []):
		uid, seen_status, email_account = saashq.db.get_value(
			"Communication", name, ["ifnull(uid, -1)", "ifnull(seen, 0)", "email_account"]
		)

		# can not mark email SEEN or UNSEEN without uid
		if not uid or uid == -1:
			continue

		seen = 1 if action == "Read" else 0
		# check if states are correct
		if (action == "Read" and seen_status == 0) or (action == "Unread" and seen_status == 1):
			create_new = True
			email_flag_queue = saashq.db.sql(
				"""select name, action from `tabEmail Flag Queue`
				where communication = %(name)s and is_completed=0""",
				{"name": name},
				as_dict=True,
			)

			for queue in email_flag_queue:
				if queue.action != action:
					saashq.delete_doc("Email Flag Queue", queue.name, ignore_permissions=True)
				elif queue.action == action:
					# Read or Unread request for email is already available
					create_new = False

			if create_new:
				flag_queue = saashq.get_doc(
					{
						"uid": uid,
						"action": action,
						"communication": name,
						"doctype": "Email Flag Queue",
						"email_account": email_account,
					}
				)
				flag_queue.save(ignore_permissions=True)
				saashq.db.set_value("Communication", name, "seen", seen, update_modified=False)
				mark_as_seen_unseen(name, action)


@saashq.whitelist()
def mark_as_closed_open(communication: str, status: str):
	"""Set status to open or close"""
	set_value("Communication", communication, "status", status)


@saashq.whitelist()
def move_email(communication: str, email_account: str):
	"""Move email to another email account."""
	set_value("Communication", communication, "email_account", email_account)


@saashq.whitelist()
def mark_as_trash(communication: str):
	"""Set email status to trash."""
	set_value("Communication", communication, "email_status", "Trash")


@saashq.whitelist()
def mark_as_spam(communication: str, sender: str):
	"""Set email status to spam."""
	email_rule = saashq.db.get_value("Email Rule", {"email_id": sender})
	if not email_rule:
		saashq.get_doc({"doctype": "Email Rule", "email_id": sender, "is_spam": 1}).insert(
			ignore_permissions=True
		)
	set_value("Communication", communication, "email_status", "Spam")


def link_communication_to_document(doc, reference_doctype, reference_name, ignore_communication_links):
	if not ignore_communication_links:
		doc.reference_doctype = reference_doctype
		doc.reference_name = reference_name
		doc.status = "Linked"
		doc.save(ignore_permissions=True)
