import saashq
from saashq.utils import validate_email_address


def execute():
	for name, email in saashq.get_all("Email Group Member", fields=["name", "email"], as_list=True):
		if not validate_email_address(email, throw=False):
			saashq.db.set_value("Email Group Member", name, "unsubscribed", 1)
			saashq.db.commit()
