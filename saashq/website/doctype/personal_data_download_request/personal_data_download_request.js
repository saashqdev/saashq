// Copyright (c) 2019, Saashq Technologies and contributors
// For license information, please see license.txt

saashq.ui.form.on("Personal Data Download Request", {
	onload: function (frm) {
		if (frm.is_new()) {
			frm.doc.user = saashq.session.user;
		}
	},
});
