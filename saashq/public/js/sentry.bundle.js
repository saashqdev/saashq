import * as Sentry from "@sentry/browser";

Sentry.init({
	dsn: saashq.boot.sentry_dsn,
	release: saashq?.boot?.versions?.saashq,
	autoSessionTracking: false,
	initialScope: {
		// don't use saashq.session.user, it's set much later and will fail because of async loading
		user: { id: saashq.boot.sitename },
		tags: { saashq_user: saashq.boot.user.name ?? "Unidentified" },
	},
	beforeSend(event, hint) {
		// Check if it was caused by saashq.throw()
		if (
			hint.originalException instanceof Error &&
			hint.originalException.stack &&
			hint.originalException.stack.includes("saashq.throw")
		) {
			return null;
		}
		return event;
	},
});
