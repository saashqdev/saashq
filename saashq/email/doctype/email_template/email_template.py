# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import json

import saashq
from saashq.model.document import Document
from saashq.utils.jinja import validate_template


class EmailTemplate(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.types import DF

		response: DF.TextEditor | None
		response_html: DF.Code | None
		subject: DF.Data
		use_html: DF.Check
	# end: auto-generated types

	@property
	def response_(self):
		return self.response_html if self.use_html else self.response

	def validate(self):
		validate_template(self.subject)
		validate_template(self.response_)

	def get_formatted_subject(self, doc):
		return saashq.render_template(self.subject, doc)

	def get_formatted_response(self, doc):
		return saashq.render_template(self.response_, doc)

	def get_formatted_email(self, doc):
		if isinstance(doc, str):
			doc = json.loads(doc)

		return {
			"subject": self.get_formatted_subject(doc),
			"message": self.get_formatted_response(doc),
		}


@saashq.whitelist()
def get_email_template(template_name, doc):
	"""Return the processed HTML of a email template with the given doc"""

	email_template = saashq.get_doc("Email Template", template_name)
	return email_template.get_formatted_email(doc)
