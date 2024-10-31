saashq.listview_settings["Prepared Report"] = {
	onload: function (list_view) {
		saashq.require("logtypes.bundle.js", () => {
			saashq.utils.logtypes.show_log_retention_message(list_view.doctype);
		});
	},
};
