// Copyright (c) 2023-Present, SaasHQ
// For license information, please see license.txt

saashq.ui.form.on("RQ Worker", {
	refresh: function (frm) {
		// Nothing in this form is supposed to be editable.
		frm.disable_form();
	},
});
