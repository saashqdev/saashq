// Copyright (c) 2023-Present, SaasHQ
// For license information, please see license.txt

saashq.ui.form.on("Print Settings", {
	print_style: function (frm) {
		saashq.db.get_value("Print Style", frm.doc.print_style, "preview").then((r) => {
			if (r.message.preview) {
				frm.get_field("print_style_preview").$wrapper.html(
					`<img src="${r.message.preview}" class="img-responsive">`
				);
			} else {
				frm.get_field("print_style_preview").$wrapper.html(
					`<p style="margin: 60px 0px" class="text-center text-muted">${__(
						"No Preview"
					)}</p>`
				);
			}
		});
	},
	onload: function (frm) {
		frm.script_manager.trigger("print_style");
	},
});
