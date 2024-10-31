import saashq
from saashq.cache_manager import clear_defaults_cache


def execute():
	saashq.db.set_default(
		"suspend_email_queue",
		saashq.db.get_default("hold_queue", "Administrator") or 0,
		parent="__default",
	)

	saashq.db.delete("DefaultValue", {"defkey": "hold_queue"})
	clear_defaults_cache()
