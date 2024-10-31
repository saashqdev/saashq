# Copyright (c) 2021, Saashq Technologies Pvt. Ltd. and Contributors
# MIT License. See LICENSE

from saashq.exceptions import ValidationError


class NewsletterAlreadySentError(ValidationError):
	pass


class NoRecipientFoundError(ValidationError):
	pass


class NewsletterNotSavedError(ValidationError):
	pass
