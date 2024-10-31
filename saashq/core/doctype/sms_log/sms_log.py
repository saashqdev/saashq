# Copyright (c) 2015, Saashq Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


from saashq.model.document import Document


class SMSLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		message: DF.SmallText | None
		no_of_requested_sms: DF.Int
		no_of_sent_sms: DF.Int
		requested_numbers: DF.Code | None
		sender_name: DF.Data | None
		sent_on: DF.Date | None
		sent_to: DF.Code | None
	# end: auto-generated types

	pass
