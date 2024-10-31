// Copyright (c) 2016, Saashq Technologies and contributors
// For license information, please see license.txt

saashq.ui.form.on("Portal Settings", {
	setup: function (frm) {
		frm.fields_dict["default_role"].get_query = function (doc) {
			return {
				filters: {
					desk_access: 0,
					disabled: 0,
				},
			};
		};
	},
	onload: function (frm) {
		frm.get_field("menu").grid.only_sortable();
	},
	refresh: function (frm) {
		frm.add_custom_button(__("Reset"), function () {
			saashq.confirm(__("Restore to default settings?"), function () {
				frm.call("reset");
			});
		});
	},
});
