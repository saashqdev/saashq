# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq
from saashq.utils import strip_html_tags
from saashq.utils.html_utils import clean_html

no_cache = 1


def get_context(context):
	message_context = saashq._dict()
	if hasattr(saashq.local, "message"):
		message_context["header"] = saashq.local.message_title
		message_context["title"] = strip_html_tags(saashq.local.message_title)
		message_context["message"] = saashq.local.message
		if hasattr(saashq.local, "message_success"):
			message_context["success"] = saashq.local.message_success

	elif saashq.local.form_dict.id:
		message_id = saashq.local.form_dict.id
		key = f"message_id:{message_id}"
		message = saashq.cache.get_value(key, expires=True)
		if message:
			message_context.update(message.get("context", {}))
			if message.get("http_status_code"):
				saashq.local.response["http_status_code"] = message["http_status_code"]

	if not message_context.title:
		message_context.title = clean_html(saashq.form_dict.title)

	if not message_context.message:
		message_context.message = clean_html(saashq.form_dict.message)

	return message_context
