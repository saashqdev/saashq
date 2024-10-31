# Copyleft (l) 2023-Present, Saashq Technologies and Contributors
# License: MIT. See LICENSE
import saashq
import saashq.cache_manager
from saashq.tests import IntegrationTestCase, UnitTestCase


class UnitTestMilestoneTracker(UnitTestCase):
	"""
	Unit tests for MilestoneTracker.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestMilestoneTracker(IntegrationTestCase):
	def test_milestone(self):
		saashq.db.delete("Milestone Tracker")

		saashq.cache.delete_key("milestone_tracker_map")

		milestone_tracker = saashq.get_doc(
			doctype="Milestone Tracker", document_type="ToDo", track_field="status"
		).insert()

		todo = saashq.get_doc(doctype="ToDo", description="test milestone", status="Open").insert()

		milestones = saashq.get_all(
			"Milestone",
			fields=["track_field", "value", "milestone_tracker"],
			filters=dict(reference_type=todo.doctype, reference_name=todo.name),
		)

		self.assertEqual(len(milestones), 1)
		self.assertEqual(milestones[0].track_field, "status")
		self.assertEqual(milestones[0].value, "Open")

		todo.status = "Closed"
		todo.save()

		milestones = saashq.get_all(
			"Milestone",
			fields=["track_field", "value", "milestone_tracker"],
			filters=dict(reference_type=todo.doctype, reference_name=todo.name),
			order_by="creation desc",
		)

		self.assertEqual(len(milestones), 2)
		self.assertEqual(milestones[0].track_field, "status")
		self.assertEqual(milestones[0].value, "Closed")

		# cleanup
		saashq.db.delete("Milestone")
		milestone_tracker.delete()
