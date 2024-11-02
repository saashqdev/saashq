// Copyright (c) 2019, Saashq Technologies and contributors
// For license information, please see license.txt

saashq.ui.form.on("Google Settings", {
	refresh: function (frm) {
		frm.dashboard.set_headline(
			__("For more information, {0}.", [
				`<a href='https://erpnexus.com/docs/user/manual/en/erpnexus_integration/google_settings'>${__(
					"Click here"
				)}</a>`,
			])
		);
	},
});
