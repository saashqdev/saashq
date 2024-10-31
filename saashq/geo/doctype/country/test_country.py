# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq
from saashq.geo.doctype.country.country import (
	get_countries_and_currencies,
	import_country_and_currency,
)
from saashq.geo.doctype.currency.currency import enable_default_currencies
from saashq.tests import IntegrationTestCase, UnitTestCase


def get_table_snapshot(doctype):
	data = saashq.db.sql(f"select * from `tab{doctype}` order by name", as_dict=True)

	inconsequential_keys = ["modified", "creation"]
	for row in data:
		for key in inconsequential_keys:
			row.pop(key, None)
	return data


class UnitTestCountry(UnitTestCase):
	"""
	Unit tests for Country.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestCountry(IntegrationTestCase):
	def test_bulk_insert_correctness(self):
		def clear_tables():
			saashq.db.delete("Currency")
			saashq.db.delete("Country")

		# Clear data
		clear_tables()

		# Reimport and verify same results
		import_country_and_currency()

		countries_before = get_table_snapshot("Country")
		currencies_before = get_table_snapshot("Currency")

		clear_tables()

		countries, currencies = get_countries_and_currencies()
		for country in countries:
			country.db_insert(ignore_if_duplicate=True)
		for currency in currencies:
			currency.db_insert(ignore_if_duplicate=True)
		enable_default_currencies()

		countries_after = get_table_snapshot("Country")
		currencies_after = get_table_snapshot("Currency")

		self.assertEqual(countries_before, countries_after)
		self.assertEqual(currencies_before, currencies_after)