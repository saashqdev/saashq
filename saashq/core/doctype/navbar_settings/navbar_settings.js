// Copyright (c) 2020, Saashq Technologies and contributors
// For license information, please see license.txt

saashq.ui.form.on("Navbar Settings", {
	after_save: function (frm) {
		saashq.ui.toolbar.clear_cache();
	},
});
