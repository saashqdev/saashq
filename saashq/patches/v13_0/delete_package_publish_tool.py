# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq


def execute():
	saashq.delete_doc("DocType", "Package Publish Tool", ignore_missing=True)
	saashq.delete_doc("DocType", "Package Document Type", ignore_missing=True)
	saashq.delete_doc("DocType", "Package Publish Target", ignore_missing=True)
