// Copyright (c) 2017, Saashq Technologies and contributors
// For license information, please see license.txt

saashq.ui.form.on("Domain Settings", {
	before_load: function (frm) {
		if (!frm.domains_multicheck) {
			frm.domains_multicheck = saashq.ui.form.make_control({
				parent: frm.fields_dict.domains_html.$wrapper,
				df: {
					fieldname: "domains_multicheck",
					fieldtype: "MultiCheck",
					get_data: () => {
						let active_domains = (frm.doc.active_domains || []).map(
							(row) => row.domain
						);
						return saashq.boot.all_domains.map((domain) => {
							return {
								label: domain,
								value: domain,
								checked: active_domains.includes(domain),
							};
						});
					},
					on_change: () => {
						frm.dirty();
					},
				},
				render_input: true,
			});
			frm.domains_multicheck.refresh_input();
		}
	},

	validate: function (frm) {
		frm.trigger("set_options_in_table");
	},

	set_options_in_table: function (frm) {
		let selected_options = frm.domains_multicheck.get_value();
		let unselected_options = frm.domains_multicheck.options
			.map((option) => option.value)
			.filter((value) => {
				return !selected_options.includes(value);
			});

		let map = {},
			list = [];
		(frm.doc.active_domains || []).map((row) => {
			map[row.domain] = row.name;
			list.push(row.domain);
		});

		unselected_options.map((option) => {
			if (list.includes(option)) {
				saashq.model.clear_doc("Has Domain", map[option]);
			}
		});

		selected_options.map((option) => {
			if (!list.includes(option)) {
				saashq.model.clear_doc("Has Domain", map[option]);
				let row = saashq.model.add_child(frm.doc, "Has Domain", "active_domains");
				row.domain = option;
			}
		});

		refresh_field("active_domains");
	},
});
