// Copyleft (l) 2023-Present, Saashq Technologies and contributors
// For license information, please see license.txt

saashq.ui.form.on("Auto Email Report", {
	refresh: function (frm) {
		frm.trigger("fetch_report_filters");
		if (!frm.is_new()) {
			frm.add_custom_button(__("Download"), function () {
				var w = window.open(
					saashq.urllib.get_full_url(
						"/api/method/saashq.email.doctype.auto_email_report.auto_email_report.download?" +
							"name=" +
							encodeURIComponent(frm.doc.name)
					)
				);
				if (!w) {
					saashq.msgprint(__("Please enable pop-ups"));
					return;
				}
			});
			frm.add_custom_button(__("Send Now"), function () {
				saashq.call({
					method: "saashq.email.doctype.auto_email_report.auto_email_report.send_now",
					args: { name: frm.doc.name },
					callback: function () {
						saashq.msgprint(__("Scheduled to send"));
					},
				});
			});
		} else {
			if (!frm.doc.user) {
				frm.set_value("user", saashq.session.user);
			}
			if (!frm.doc.email_to) {
				frm.set_value("email_to", saashq.session.user);
			}
		}

		frm.set_query("sender", function () {
			return {
				filters: {
					enable_outgoing: 1,
					awaiting_password: 0,
				},
			};
		});
	},
	report: function (frm) {
		frm.set_value("filters", "");
		frm.trigger("fetch_report_filters");
	},
	fetch_report_filters(frm) {
		if (
			frm.doc.report &&
			frm.doc.report_type !== "Report Builder" &&
			frm.script_setup_for !== frm.doc.report
		) {
			saashq.call({
				method: "saashq.desk.query_report.get_script",
				args: {
					report_name: frm.doc.report,
				},
				callback: function (r) {
					saashq.dom.eval(r.message.script || "");
					frm.script_setup_for = frm.doc.report;
					frm.trigger("show_filters");
				},
			});
		} else {
			frm.trigger("show_filters");
		}
	},
	show_filters: async function (frm) {
		if (!frm.doc.report) {
			return;
		}
		var wrapper = $(frm.get_field("filters_display").wrapper);
		wrapper.empty();
		let reference_report = saashq.query_reports[frm.doc.report];
		if (!reference_report || !reference_report.filters) {
			reference_report = await saashq.model.with_doc("Report", frm.doc.report);
		}
		if (
			frm.doc.report_type === "Custom Report" ||
			(frm.doc.report_type !== "Report Builder" &&
				reference_report &&
				reference_report.filters)
		) {
			// make a table to show filters
			var table = $(
				'<table class="table table-bordered" style="cursor:pointer; margin:0px;"><thead>\
				<tr><th style="width: 50%">' +
					__("Filter") +
					"</th><th>" +
					__("Value") +
					"</th></tr>\
				</thead><tbody></tbody></table>"
			).appendTo(wrapper);
			$('<p class="text-muted small">' + __("Click table to edit") + "</p>").appendTo(
				wrapper
			);

			var filters = {};

			let report_filters;

			if (
				frm.doc.report_type === "Custom Report" &&
				reference_report &&
				reference_report.filters
			) {
				if (frm.doc.filters) {
					filters = JSON.parse(frm.doc.filters);
				} else {
					saashq.db.get_value("Report", frm.doc.report, "json", (r) => {
						if (r && r.json) {
							filters = JSON.parse(r.json).filters || {};
						}
					});
				}

				report_filters = saashq.query_reports[frm.doc.reference_report].filters;
			} else {
				filters = JSON.parse(frm.doc.filters || "{}");
				report_filters = reference_report.filters;
			}

			if (report_filters && report_filters.length > 0) {
				frm.set_value("filter_meta", JSON.stringify(report_filters));
				if (frm.is_dirty()) {
					frm.save();
				}
			}

			var report_filters_list = [];
			$.each(report_filters, function (key, val) {
				// Remove break fieldtype from the filters
				if (val.fieldtype != "Break") {
					report_filters_list.push(val);
				}
			});
			report_filters = report_filters_list;

			const mandatory_css = {
				"background-color": "var(--error-bg)",
				"font-weight": "bold",
			};

			report_filters.forEach((f) => {
				const css = f.reqd ? mandatory_css : {};
				const row = $("<tr></tr>").appendTo(table.find("tbody"));
				$("<td>" + f.label + "</td>").appendTo(row);
				$("<td>" + saashq.format(filters[f.fieldname], f) + "</td>")
					.css(css)
					.appendTo(row);
			});

			table.on("click", function () {
				var dialog = new saashq.ui.Dialog({
					fields: report_filters,
					primary_action: function () {
						var values = this.get_values();
						if (values) {
							this.hide();
							frm.set_value("filters", JSON.stringify(values));
							frm.trigger("show_filters");
						}
					},
				});
				dialog.show();
				dialog.set_values(filters);
			});

			// populate dynamic date field selection
			let date_fields = report_filters
				.filter((df) => df.fieldtype === "Date")
				.map((df) => ({ label: df.label, value: df.fieldname }));
			frm.set_df_property("from_date_field", "options", date_fields);
			frm.set_df_property("to_date_field", "options", date_fields);
			frm.toggle_display("dynamic_report_filters_section", date_fields.length > 0);
		}
	},
});
