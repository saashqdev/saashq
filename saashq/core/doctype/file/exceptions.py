import saashq


class MaxFileSizeReachedError(saashq.ValidationError):
	pass


class FolderNotEmpty(saashq.ValidationError):
	pass


class FileTypeNotAllowed(saashq.ValidationError):
	pass


from saashq.exceptions import *
