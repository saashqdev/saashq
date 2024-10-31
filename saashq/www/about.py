# Copyright (c) 2015, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import saashq

sitemap = 1


def get_context(context):
	context.doc = saashq.get_cached_doc("About Us Settings")

	return context
