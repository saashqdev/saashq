# Copyright (c) 2021, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

from click import secho

import saashq


def execute():
	if saashq.get_hooks("jenv"):
		print()
		secho(
			'WARNING: The hook "jenv" is deprecated. Follow the migration guide to use the new "jinja" hook.',
			fg="yellow",
		)
		secho("https://github.com/saashqdev/saashq/wiki/Migrating-to-Version-13", fg="yellow")
		print()
