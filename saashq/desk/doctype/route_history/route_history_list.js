saashq.listview_settings["Route History"] = {
	onload: function (listview) {
		saashq.require("logtypes.bundle.js", () => {
			saashq.utils.logtypes.show_log_retention_message(cur_list.doctype);
		});
	},
};
