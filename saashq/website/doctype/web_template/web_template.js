// Copyright (c) 2023-Present, SaasHQ
// For license information, please see license.txt

saashq.ui.form.on("Web Template", {
	refresh: function (frm) {
		if (!saashq.boot.developer_mode && frm.doc.standard) {
			frm.disable_form();
		}

		frm.toggle_display("standard", saashq.boot.developer_mode);
		// necessary to show template field again, after it was hidden when
		// unchecking 'standard'.
		frm.toggle_display("template", !frm.doc.standard);
	},
	standard: function (frm) {
		if (!frm.doc.standard && !frm.is_new()) {
			// If standard changes from true to false, hide template until
			// the next save. Changes will get overwritten from the backend
			// on save and should not be possible in the UI.
			frm.toggle_display("template", false);
			frm.dashboard.clear_headline();
			frm.dashboard.set_headline(__("Please save to edit the template."));
		}
	},
});
