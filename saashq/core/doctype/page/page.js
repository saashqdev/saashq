// Copyright (c) 2023-Present, SaasHQ
// For license information, please see license.txt

saashq.ui.form.on("Page", {
	refresh: function (frm) {
		if (!saashq.boot.developer_mode && saashq.session.user != "Administrator") {
			// make the document read-only
			frm.set_read_only();
		}
		if (!frm.is_new() && !frm.doc.istable) {
			frm.add_custom_button(__("Go to {0} Page", [frm.doc.title || frm.doc.name]), () => {
				saashq.set_route(frm.doc.name);
			});
		}
	},
});
