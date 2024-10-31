import saashq
from saashq.desk.doctype.tag.tag import add_tag
from saashq.desk.reportview import get_stats
from saashq.tests import IntegrationTestCase, UnitTestCase


class UnitTestTag(UnitTestCase):
	"""
	Unit tests for Tag.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestTag(IntegrationTestCase):
	def setUp(self) -> None:
		saashq.db.delete("Tag")
		saashq.db.sql("UPDATE `tabDocType` set _user_tags=''")

	def test_tag_count_query(self):
		self.assertDictEqual(
			get_stats('["_user_tags"]', "DocType"),
			{"_user_tags": [["No Tags", saashq.db.count("DocType")]]},
		)
		add_tag("Standard", "DocType", "User")
		add_tag("Standard", "DocType", "ToDo")

		# count with no filter
		self.assertDictEqual(
			get_stats('["_user_tags"]', "DocType"),
			{"_user_tags": [["Standard", 2], ["No Tags", saashq.db.count("DocType") - 2]]},
		)

		# count with child table field filter
		self.assertDictEqual(
			get_stats(
				'["_user_tags"]',
				"DocType",
				filters='[["DocField", "fieldname", "like", "%last_name%"], ["DocType", "name", "like", "%use%"]]',
			),
			{"_user_tags": [["Standard", 1], ["No Tags", 0]]},
		)
