# Copyright (c) 2020, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import saashq


def execute():
	saashq.delete_doc("DocType", "Package Publish Tool", ignore_missing=True)
	saashq.delete_doc("DocType", "Package Document Type", ignore_missing=True)
	saashq.delete_doc("DocType", "Package Publish Target", ignore_missing=True)
