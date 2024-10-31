# Copyright (c) 2015, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import saashq


def execute():
	saashq.delete_doc_if_exists("DocType", "User Permission for Page and Report")
