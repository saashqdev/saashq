saashq.pages["backups"].on_page_load = function (wrapper) {
	var page = saashq.ui.make_app_page({
		parent: wrapper,
		title: __("Download Backups"),
		single_column: true,
	});

	page.add_inner_button(__("Set Number of Backups"), function () {
		saashq.set_route("Form", "System Settings");
	});

	page.add_inner_button(__("Download Files Backup"), function () {
		saashq.call({
			method: "saashq.desk.page.backups.backups.schedule_files_backup",
			args: { user_email: saashq.session.user_email },
		});
	});

	page.add_inner_button(__("Get Backup Encryption Key"), function () {
		if (saashq.user.has_role("System Manager")) {
			saashq.verify_password(function () {
				saashq.call({
					method: "saashq.utils.backups.get_backup_encryption_key",
					callback: function (r) {
						saashq.msgprint({
							title: __("Backup Encryption Key"),
							message: __(r.message),
							indicator: "blue",
						});
					},
				});
			});
		} else {
			saashq.msgprint({
				title: __("Error"),
				message: __("System Manager privileges required."),
				indicator: "red",
			});
		}
	});

	saashq.breadcrumbs.add("Setup");

	$(saashq.render_template("backups")).appendTo(page.body.addClass("no-border"));
};
