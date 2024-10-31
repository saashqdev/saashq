// Copyleft (l) 2023-Present, Saashq Technologies and contributors
// For license information, please see license.txt

saashq.ui.form.on("Notification Settings", {
	onload: (frm) => {
		frm.set_query("subscribed_documents", () => {
			return {
				filters: {
					istable: 0,
				},
			};
		});
	},

	refresh: (frm) => {
		if (saashq.user.has_role("System Manager")) {
			frm.add_custom_button(__("Go to Notification Settings List"), () => {
				saashq.set_route("List", "Notification Settings");
			});
		}
	},
});
