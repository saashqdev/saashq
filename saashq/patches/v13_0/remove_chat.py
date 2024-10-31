import click

import saashq


def execute():
	saashq.delete_doc_if_exists("DocType", "Chat Message")
	saashq.delete_doc_if_exists("DocType", "Chat Message Attachment")
	saashq.delete_doc_if_exists("DocType", "Chat Profile")
	saashq.delete_doc_if_exists("DocType", "Chat Token")
	saashq.delete_doc_if_exists("DocType", "Chat Room User")
	saashq.delete_doc_if_exists("DocType", "Chat Room")
	saashq.delete_doc_if_exists("Module Def", "Chat")

	click.secho(
		"Chat Module is moved to a separate app and is removed from Saashq in version-13.\n"
		"Please install the app to continue using the chat feature: https://github.com/saashqdev/chat",
		fg="yellow",
	)
