# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

"""docfield utililtes"""

import saashq


def supports_translation(fieldtype):
	return fieldtype in ["Data", "Select", "Text", "Small Text", "Text Editor"]
