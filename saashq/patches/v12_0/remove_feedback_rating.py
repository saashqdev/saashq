import saashq


def execute():
	"""
	Deprecate Feedback Trigger and Rating. This feature was not customizable.
	Now can be achieved via custom Web Forms
	"""
	saashq.delete_doc("DocType", "Feedback Trigger")
	saashq.delete_doc("DocType", "Feedback Rating")
