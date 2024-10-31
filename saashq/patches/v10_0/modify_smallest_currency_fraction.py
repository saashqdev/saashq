# Copyright (c) 2018, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import saashq


def execute():
	saashq.db.set_value("Currency", "USD", "smallest_currency_fraction_value", "0.01")
