# Copyleft (l) 2023-Present, SaasHQ and contributors
# License: MIT. See LICENSE

import imaplib
import poplib

from saashq.utils import cint


def get_port(doc):
	if not doc.incoming_port:
		if doc.use_imap:
			doc.incoming_port = imaplib.IMAP4_SSL_PORT if doc.use_ssl else imaplib.IMAP4_PORT

		else:
			doc.incoming_port = poplib.POP3_SSL_PORT if doc.use_ssl else poplib.POP3_PORT

	return cint(doc.incoming_port)
