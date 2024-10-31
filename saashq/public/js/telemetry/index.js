import "../lib/posthog.js";

class TelemetryManager {
	constructor() {
		this.enabled = false;

		this.project_id = saashq.boot.posthog_project_id;
		this.telemetry_host = saashq.boot.posthog_host;
		this.site_age = saashq.boot.telemetry_site_age;
		if (cint(saashq.boot.enable_telemetry) && this.project_id && this.telemetry_host) {
			this.enabled = true;
		}
	}

	initialize() {
		if (!this.enabled) return;
		let disable_decide = !this.should_record_session();
		try {
			posthog.init(this.project_id, {
				api_host: this.telemetry_host,
				autocapture: false,
				capture_pageview: false,
				capture_pageleave: false,
				advanced_disable_decide: disable_decide,
			});
			posthog.identify(saashq.boot.sitename);
			this.send_heartbeat();
			this.register_pageview_handler();
		} catch (e) {
			console.trace("Failed to initialize telemetry", e);
			this.enabled = false;
		}
	}

	capture(event, app, props) {
		if (!this.enabled) return;
		posthog.capture(`${app}_${event}`, props);
	}

	disable() {
		this.enabled = false;
	}

	can_enable() {
		if (cint(navigator.doNotTrack)) {
			return false;
		}
		let posthog_available = Boolean(this.telemetry_host && this.project_id);
		let sentry_available = Boolean(saashq.boot.sentry_dsn);
		return posthog_available || sentry_available;
	}

	send_heartbeat() {
		const KEY = "ph_last_heartbeat";
		const now = saashq.datetime.system_datetime(true);
		const last = localStorage.getItem(KEY);

		if (!last || moment(now).diff(moment(last), "hours") > 12) {
			localStorage.setItem(KEY, now.toISOString());
			this.capture("heartbeat", "saashq", { saashq_version: saashq.boot?.versions?.saashq });
		}
	}

	register_pageview_handler() {
		if (this.site_age && this.site_age > 6) {
			return;
		}

		saashq.router.on("change", () => {
			posthog.capture("$pageview");
		});
	}

	should_record_session() {
		let start = saashq.boot.sysdefaults.session_recording_start;
		if (!start) return;

		let start_datetime = saashq.datetime.str_to_obj(start);
		let now = saashq.datetime.now_datetime();
		// if user allowed recording only record for first 2 hours, never again.
		return saashq.datetime.get_minute_diff(now, start_datetime) < 120;
	}
}

saashq.telemetry = new TelemetryManager();
saashq.telemetry.initialize();
