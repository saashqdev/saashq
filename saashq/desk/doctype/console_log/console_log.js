// Copyright (c) 2020, Saashq Technologies and contributors
// For license information, please see license.txt

saashq.ui.form.on("Console Log", {
	refresh: function (frm) {
		frm.add_custom_button(__("Re-Run in Console"), () => {
			window.localStorage.setItem("system_console_code", frm.doc.script);
			window.localStorage.setItem("system_console_type", frm.doc.type);
			saashq.set_route("Form", "System Console");
		});
	},
});
