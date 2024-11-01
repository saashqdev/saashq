# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq
from saashq.model.document import Document
from saashq.query_builder import Interval
from saashq.query_builder.functions import Now


class ScheduledJobLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		debug_log: DF.Code | None
		details: DF.Code | None
		scheduled_job_type: DF.Link
		status: DF.Literal["Scheduled", "Complete", "Failed"]
	# end: auto-generated types

	@staticmethod
	def clear_old_logs(days=90):
		table = saashq.qb.DocType("Scheduled Job Log")
		saashq.db.delete(table, filters=(table.creation < (Now() - Interval(days=days))))
