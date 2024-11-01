# Copyright (c) 2023-Present, SaasHQ
# MIT License. See license.txt


import functools

import saashq


@saashq.whitelist()
def get_google_fonts():
	return _get_google_fonts()


@functools.lru_cache
def _get_google_fonts():
	file_path = saashq.get_app_path("saashq", "data", "google_fonts.json")
	return saashq.parse_json(saashq.read_file(file_path))
