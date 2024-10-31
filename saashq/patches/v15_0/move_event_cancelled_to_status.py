import saashq


def execute():
	Event = saashq.qb.DocType("Event")
	query = (
		saashq.qb.update(Event)
		.set(Event.event_type, "Private")
		.set(Event.status, "Cancelled")
		.where(Event.event_type == "Cancelled")
	)
	query.run()
