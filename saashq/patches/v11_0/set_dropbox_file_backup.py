import saashq
from saashq.utils import cint


def execute():
	saashq.reload_doctype("Dropbox Settings")
	check_dropbox_enabled = cint(saashq.db.get_single_value("Dropbox Settings", "enabled"))
	if check_dropbox_enabled == 1:
		saashq.db.set_single_value("Dropbox Settings", "file_backup", 1)
