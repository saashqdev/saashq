import saashq
from saashq import format
from saashq.tests import IntegrationTestCase


class TestFormatter(IntegrationTestCase):
	def test_currency_formatting(self):
		df = saashq._dict({"fieldname": "amount", "fieldtype": "Currency", "options": "currency"})

		doc = saashq._dict({"amount": 5})
		saashq.db.set_default("currency", "INR")

		# if currency field is not passed then default currency should be used.
		self.assertEqual(format(100000, df, doc, format="#,###.##"), "₹ 100,000.00")

		doc.currency = "USD"
		self.assertEqual(format(100000, df, doc, format="#,###.##"), "$ 100,000.00")

		saashq.db.set_default("currency", None)
