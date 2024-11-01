# Copyright (c) 2023-Present, SaasHQ
# MIT License. See LICENSE

from saashq.exceptions import ValidationError


class NewsletterAlreadySentError(ValidationError):
	pass


class NoRecipientFoundError(ValidationError):
	pass


class NewsletterNotSavedError(ValidationError):
	pass
