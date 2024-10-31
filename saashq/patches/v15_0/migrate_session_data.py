import saashq
from saashq.utils import update_progress_bar


def execute():
	saashq.db.auto_commit_on_many_writes = True

	Sessions = saashq.qb.DocType("Sessions")

	current_sessions = (saashq.qb.from_(Sessions).select(Sessions.sid, Sessions.sessiondata)).run(
		as_dict=True
	)

	for i, session in enumerate(current_sessions):
		try:
			new_data = saashq.as_json(saashq.safe_eval(session.sessiondata))
		except Exception:
			# Rerunning patch or already converted.
			continue

		(
			saashq.qb.update(Sessions).where(Sessions.sid == session.sid).set(Sessions.sessiondata, new_data)
		).run()
		update_progress_bar("Patching sessions", i, len(current_sessions))
