# Copyright (c) 2015, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import saashq
from saashq.model.document import Document

DEFAULT_ENABLED_CURRENCIES = ("INR", "USD", "GBP", "EUR", "AED", "AUD", "JPY", "CNY", "CHF")


class Currency(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		currency_name: DF.Data
		enabled: DF.Check
		fraction: DF.Data | None
		fraction_units: DF.Int
		number_format: DF.Literal[
			"",
			"#,###.##",
			"#.###,##",
			"# ###.##",
			"# ###,##",
			"#'###.##",
			"#, ###.##",
			"#,##,###.##",
			"#,###.###",
			"#.###",
			"#,###",
		]
		smallest_currency_fraction_value: DF.Currency
		symbol: DF.Data | None
		symbol_on_right: DF.Check
	# end: auto-generated types

	# NOTE: During installation country docs are bulk inserted.
	def validate(self):
		saashq.clear_cache()


def enable_default_currencies():
	saashq.db.set_value("Currency", {"name": ("in", DEFAULT_ENABLED_CURRENCIES)}, "enabled", 1)
