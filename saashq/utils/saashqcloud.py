import saashq

SAASHQ_CLOUD_DOMAINS = ("saashq.cloud", "erpnexus.com", "saashqhr.com")


def on_saashqcloud() -> bool:
	"""Returns true if running on Saashq Cloud.


	Useful for modifying few features for better UX."""
	return saashq.local.site.endswith(SAASHQ_CLOUD_DOMAINS)
