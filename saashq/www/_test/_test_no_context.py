import saashq


# no context object is accepted
def get_context():
	context = saashq._dict()
	context.body = "Custom Content"
	return context
