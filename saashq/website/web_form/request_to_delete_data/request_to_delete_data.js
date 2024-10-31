saashq.ready(function () {
	saashq.web_form.after_load = () => {
		saashq.call({
			method: "saashq.website.doctype.website_settings.website_settings.get_auto_account_deletion",
			callback: (data) => {
				if (data.message) {
					const intro_wrapper = $("#introduction .ql-editor.read-mode");
					const sla_description = __(
						"Note: Your request for account deletion will be fulfilled within {0} hours.",
						[data.message]
					);
					const sla_description_wrapper = `<br><b>${sla_description}</b>`;
					intro_wrapper.html(intro_wrapper.html() + sla_description_wrapper);
				}
			},
		});
	};
});
