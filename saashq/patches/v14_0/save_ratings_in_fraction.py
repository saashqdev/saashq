import saashq
from saashq.query_builder import DocType


def execute():
	RATING_FIELD_TYPE = "decimal(3,2)"
	rating_fields = saashq.get_all(
		"DocField", fields=["parent", "fieldname"], filters={"fieldtype": "Rating"}
	)

	custom_rating_fields = saashq.get_all(
		"Custom Field", fields=["dt", "fieldname"], filters={"fieldtype": "Rating"}
	)

	for _field in rating_fields + custom_rating_fields:
		doctype_name = _field.get("parent") or _field.get("dt")
		doctype = DocType(doctype_name)
		field = _field.fieldname

		# TODO: Add postgres support (for the check)
		if (
			saashq.conf.db_type == "mariadb"
			and saashq.db.get_column_type(doctype_name, field) == RATING_FIELD_TYPE
		):
			continue

		# commit any changes so far for upcoming DDL
		saashq.db.commit()

		# alter column types for rating fieldtype
		saashq.db.change_column_type(doctype_name, column=field, type=RATING_FIELD_TYPE, nullable=True)

		# update data: int => decimal
		saashq.qb.update(doctype).set(doctype[field], doctype[field] / 5).run()

		# commit to flush updated rows
		saashq.db.commit()
