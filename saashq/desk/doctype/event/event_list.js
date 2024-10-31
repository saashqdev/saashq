saashq.listview_settings["Event"] = {
	add_fields: ["starts_on", "ends_on"],
	onload: function () {
		saashq.route_options = {
			status: "Open",
		};
	},
};
