import saashq
import saashq.share


def execute():
	for user in saashq.STANDARD_USERS:
		saashq.share.remove("User", user, user)
