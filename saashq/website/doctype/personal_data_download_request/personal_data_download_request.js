// Copyright (c) 2023-Present, SaasHQ
// For license information, please see license.txt

saashq.ui.form.on("Personal Data Download Request", {
	onload: function (frm) {
		if (frm.is_new()) {
			frm.doc.user = saashq.session.user;
		}
	},
});
