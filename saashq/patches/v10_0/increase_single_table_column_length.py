"""
Run this after updating country_info.json and or
"""
import saashq


def execute():
	for col in ("field", "doctype"):
		saashq.db.sql_ddl(f"alter table `tabSingles` modify column `{col}` varchar(255)")
