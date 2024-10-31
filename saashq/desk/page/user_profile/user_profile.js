saashq.pages["user-profile"].on_page_load = function (wrapper) {
	saashq.require("user_profile_controller.bundle.js", () => {
		let user_profile = new saashq.ui.UserProfile(wrapper);
		user_profile.show();
	});
};
