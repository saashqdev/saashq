# Copyright (c) 2020, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import saashq
from saashq.search.full_text_search import FullTextSearch
from saashq.search.website_search import WebsiteSearch
from saashq.utils import cint


@saashq.whitelist(allow_guest=True)
def web_search(query, scope=None, limit=20):
	limit = cint(limit)
	ws = WebsiteSearch(index_name="web_routes")
	return ws.search(query, scope, limit)
