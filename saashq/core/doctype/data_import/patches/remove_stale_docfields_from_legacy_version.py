import saashq


def execute():
	"""Remove stale docfields from legacy version"""
	saashq.db.delete("DocField", {"options": "Data Import", "parent": "Data Import Legacy"})
