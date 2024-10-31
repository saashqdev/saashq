// Copyleft (l) 2023-Present, Saashq Technologies and contributors
// For license information, please see license.txt

saashq.ui.form.on("Network Printer Settings", {
	onload(frm) {
		frm.trigger("connect_print_server");
	},
	server_ip(frm) {
		frm.trigger("connect_print_server");
	},
	port(frm) {
		frm.trigger("connect_print_server");
	},
	connect_print_server(frm) {
		if (frm.doc.server_ip && frm.doc.port) {
			saashq.call({
				doc: frm.doc,
				method: "get_printers_list",
				args: {
					ip: frm.doc.server_ip,
					port: frm.doc.port,
				},
				callback: function (data) {
					frm.set_df_property("printer_name", "options", [""].concat(data.message));
				},
			});
		}
	},
});
