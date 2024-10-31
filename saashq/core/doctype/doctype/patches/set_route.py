import saashq
from saashq.desk.utils import slug


def execute():
	for doctype in saashq.get_all("DocType", ["name", "route"], dict(istable=0)):
		if not doctype.route:
			saashq.db.set_value("DocType", doctype.name, "route", slug(doctype.name), update_modified=False)
