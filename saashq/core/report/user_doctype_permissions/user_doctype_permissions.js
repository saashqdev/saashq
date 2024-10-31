// Copyright (c) 2024, Saashq Technologies and contributors
// For license information, please see license.txt

saashq.query_reports["User Doctype Permissions"] = {
	filters: [
		{
			fieldname: "user",
			label: __("User"),
			fieldtype: "Link",
			options: "User",
			reqd: 1,
		},
	],
};
