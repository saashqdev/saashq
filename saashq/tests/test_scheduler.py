import os
import time
from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import patch

import saashq
from saashq.core.doctype.scheduled_job_type.scheduled_job_type import ScheduledJobType, sync_jobs
from saashq.tests import IntegrationTestCase
from saashq.utils import add_days, get_datetime
from saashq.utils.data import now_datetime
from saashq.utils.doctor import purge_pending_jobs
from saashq.utils.scheduler import (
	DEFAULT_SCHEDULER_TICK,
	_get_last_creation_timestamp,
	enqueue_events,
	is_dormant,
	schedule_jobs_based_on_activity,
	sleep_duration,
)


def test_timeout_10():
	time.sleep(10)


def test_method():
	pass


class TestScheduler(IntegrationTestCase):
	def setUp(self):
		saashq.db.rollback()

		if not os.environ.get("CI"):
			return

		purge_pending_jobs()
		if not saashq.get_all("Scheduled Job Type", limit=1):
			sync_jobs()

	def tearDown(self):
		purge_pending_jobs()

	def test_enqueue_jobs(self):
		saashq.db.sql("update `tabScheduled Job Type` set last_execution = '2010-01-01 00:00:00'")

		enqueued_jobs = enqueue_events()

		self.assertIn("saashq.desk.notifications.clear_notifications", enqueued_jobs)
		self.assertIn("saashq.utils.change_log.check_for_update", enqueued_jobs)
		self.assertIn(
			"saashq.email.doctype.auto_email_report.auto_email_report.send_monthly",
			enqueued_jobs,
		)

	def test_queue_peeking(self):
		job = get_test_job()

		with patch.object(job, "is_job_in_queue", return_value=True):
			# 1st job is in the queue (or running), don't enqueue it again
			self.assertFalse(job.enqueue())

	def test_is_dormant(self):
		self.assertTrue(is_dormant(check_time=get_datetime("2100-01-01 00:00:00")))
		self.assertTrue(is_dormant(check_time=add_days(saashq.db.get_last_created("Activity Log"), 5)))
		self.assertFalse(is_dormant(check_time=saashq.db.get_last_created("Activity Log")))

	def test_once_a_day_for_dormant(self):
		saashq.db.truncate("Scheduled Job Log")
		self.assertTrue(schedule_jobs_based_on_activity(check_time=get_datetime("2100-01-01 00:00:00")))
		self.assertTrue(
			schedule_jobs_based_on_activity(
				check_time=add_days(saashq.db.get_last_created("Activity Log"), 5)
			)
		)

		# create a fake job executed 5 days from now
		job = get_test_job(method="saashq.tests.test_scheduler.test_method", frequency="Daily")
		job.execute()
		job_log = saashq.get_doc("Scheduled Job Log", dict(scheduled_job_type=job.name))
		job_log.db_set(
			"creation", add_days(_get_last_creation_timestamp("Activity Log"), 5), update_modified=False
		)
		schedule_jobs_based_on_activity.clear_cache()

		# inactive site with recent job, don't run
		self.assertFalse(
			schedule_jobs_based_on_activity(
				check_time=add_days(_get_last_creation_timestamp("Activity Log"), 5)
			)
		)

		# one more day has passed
		self.assertTrue(
			schedule_jobs_based_on_activity(
				check_time=add_days(_get_last_creation_timestamp("Activity Log"), 6)
			)
		)

	def test_real_time_alignment(self):
		test_cases = {
			timedelta(minutes=0): DEFAULT_SCHEDULER_TICK,
			timedelta(minutes=0, seconds=12): DEFAULT_SCHEDULER_TICK - 12,
			timedelta(minutes=1, seconds=12): DEFAULT_SCHEDULER_TICK - (1 * 60 + 12),
			timedelta(hours=23, minutes=59): 60,
			timedelta(hours=23, minutes=59, seconds=30): 30,
			timedelta(minutes=0, seconds=1): DEFAULT_SCHEDULER_TICK - 1,
			timedelta(minutes=2): DEFAULT_SCHEDULER_TICK - 2 * 60,
		}
		for delta, expected_sleep in test_cases.items():
			fake_time = datetime(2024, 1, 1) + delta
			with self.freeze_time(fake_time, is_utc=True):
				self.assertEqual(sleep_duration(DEFAULT_SCHEDULER_TICK), expected_sleep, delta)


def get_test_job(method="saashq.tests.test_scheduler.test_timeout_10", frequency="All") -> ScheduledJobType:
	if not saashq.db.exists("Scheduled Job Type", dict(method=method)):
		job = saashq.get_doc(
			doctype="Scheduled Job Type",
			method=method,
			last_execution="2010-01-01 00:00:00",
			frequency=frequency,
		).insert()
	else:
		job = saashq.get_doc("Scheduled Job Type", dict(method=method))
		job.db_set("last_execution", "2010-01-01 00:00:00")
		job.db_set("frequency", frequency)
	saashq.db.commit()

	return job
