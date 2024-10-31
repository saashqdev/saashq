# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE
from saashq import _

no_cache = 1


def get_context(context):
	context.no_breadcrumbs = True
	context.parents = [{"name": "me", "title": _("My Account")}]
