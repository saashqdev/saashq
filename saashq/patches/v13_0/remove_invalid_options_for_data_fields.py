# Copyright (c) 2022, Saashq and Contributors
# License: MIT. See LICENSE


import saashq
from saashq.model import data_field_options


def execute():
	custom_field = saashq.qb.DocType("Custom Field")
	(
		saashq.qb.update(custom_field)
		.set(custom_field.options, None)
		.where((custom_field.fieldtype == "Data") & (custom_field.options.notin(data_field_options)))
	).run()
