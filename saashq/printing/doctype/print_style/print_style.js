// Copyright (c) 2023-Present, SaasHQ
// For license information, please see license.txt

saashq.ui.form.on("Print Style", {
	refresh: function (frm) {
		frm.add_custom_button(__("Print Settings"), () => {
			saashq.set_route("Form", "Print Settings");
		});
	},
});
