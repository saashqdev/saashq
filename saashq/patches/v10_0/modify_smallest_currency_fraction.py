# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq


def execute():
	saashq.db.set_value("Currency", "USD", "smallest_currency_fraction_value", "0.01")
