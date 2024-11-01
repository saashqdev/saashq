// Copyright (c) 2023-Present, SaasHQ
// For license information, please see license.txt

saashq.ui.form.on("Bulk Update", {
	refresh: function (frm) {
		frm.set_query("document_type", function () {
			return {
				filters: [
					["DocType", "issingle", "=", 0],
					["DocType", "name", "not in", saashq.model.core_doctypes_list],
				],
			};
		});

		frm.page.set_primary_action(__("Update"), function () {
			if (!frm.doc.update_value) {
				saashq.throw(__('Field "value" is mandatory. Please specify value to be updated'));
			} else {
				frm.call("bulk_update").then((r) => {
					let failed = r.message;
					if (!failed) failed = [];

					if (failed.length && !r._server_messages) {
						saashq.throw(
							__("Cannot update {0}", [
								failed.map((f) => (f.bold ? f.bold() : f)).join(", "),
							])
						);
					} else {
						saashq.msgprint({
							title: __("Success"),
							message: __("Updated Successfully"),
							indicator: "green",
						});
					}

					saashq.hide_progress();
					frm.save();
				});
			}
		});
	},

	document_type: function (frm) {
		// set field options
		if (!frm.doc.document_type) return;

		saashq.model.with_doctype(frm.doc.document_type, function () {
			var options = $.map(saashq.get_meta(frm.doc.document_type).fields, function (d) {
				if (d.fieldname && saashq.model.no_value_type.indexOf(d.fieldtype) === -1) {
					return d.fieldname;
				}
				return null;
			});
			frm.set_df_property("field", "options", options);
		});
	},
});
