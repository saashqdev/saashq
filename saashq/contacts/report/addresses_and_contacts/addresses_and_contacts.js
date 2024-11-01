// Copyright (c) 2023-Present, SaasHQ
// For license information, please see license.txt

saashq.query_reports["Addresses And Contacts"] = {
	filters: [
		{
			reqd: 1,
			fieldname: "reference_doctype",
			label: __("Entity Type"),
			fieldtype: "Link",
			options: "DocType",
			get_query: function () {
				return {
					filters: {
						name: ["in", "Contact, Address"],
					},
				};
			},
		},
		{
			fieldname: "reference_name",
			label: __("Entity Name"),
			fieldtype: "Dynamic Link",
			get_options: function () {
				let reference_doctype = saashq.query_report.get_filter_value("reference_doctype");
				if (!reference_doctype) {
					saashq.throw(__("Please select Entity Type first"));
				}
				return reference_doctype;
			},
		},
	],
};
