// Copyright (c) 2024, Saashq Technologies and contributors
// For license information, please see license.txt

saashq.ui.form.on("Workspace Settings", {
	setup(frm) {
		frm.hide_full_form_button = true;
		frm.docfields = [];
		frm.workspace_map = {};
		let workspace_visibilty = JSON.parse(frm.doc.workspace_visibility_json || "{}");

		// build fields from workspaces
		let cnt = 0,
			column_added = false;
		for (let page of saashq.boot.allowed_workspaces) {
			if (page.public) {
				frm.workspace_map[page.name] = page;
				cnt++;
				frm.docfields.push({
					fieldtype: "Check",
					fieldname: page.name,
					hidden: !saashq.boot.app_data_map[saashq.current_app].workspaces.includes(
						page.title
					),
					label: page.title + (page.parent_page ? ` (${page.parent_page})` : ""),
					initial_value: workspace_visibilty[page.name] !== 0, // not set is also visible
				});
			}
		}

		saashq.temp = frm;
	},
	validate(frm) {
		frm.doc.workspace_visibility_json = JSON.stringify(frm.dialog.get_values());
		frm.doc.workspace_setup_completed = 1;
	},
	after_save(frm) {
		// reload page to show latest sidebar
		saashq.app.sidebar.reload();
	},
});
