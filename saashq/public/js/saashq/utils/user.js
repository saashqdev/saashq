saashq.user_info = function (uid) {
	if (!uid) uid = saashq.session.user;

	let user_info;
	if (!(saashq.boot.user_info && saashq.boot.user_info[uid])) {
		user_info = { fullname: uid || "Unknown" };
	} else {
		user_info = saashq.boot.user_info[uid];
	}

	user_info.abbr = saashq.get_abbr(user_info.fullname);
	user_info.color = saashq.get_palette(user_info.fullname);

	return user_info;
};

saashq.update_user_info = function (user_info) {
	for (let user in user_info) {
		if (saashq.boot.user_info[user]) {
			Object.assign(saashq.boot.user_info[user], user_info[user]);
		} else {
			saashq.boot.user_info[user] = user_info[user];
		}
	}
};

saashq.provide("saashq.user");

$.extend(saashq.user, {
	name: "Guest",
	full_name: function (uid) {
		return uid === saashq.session.user
			? __(
					"You",
					null,
					"Name of the current user. For example: You edited this 5 hours ago."
			  )
			: saashq.user_info(uid).fullname;
	},
	image: function (uid) {
		return saashq.user_info(uid).image;
	},
	abbr: function (uid) {
		return saashq.user_info(uid).abbr;
	},
	has_role: function (rl) {
		if (typeof rl == "string") rl = [rl];
		for (var i in rl) {
			if ((saashq.boot ? saashq.boot.user.roles : ["Guest"]).indexOf(rl[i]) != -1)
				return true;
		}
	},
	get_desktop_items: function () {
		// hide based on permission
		var modules_list = $.map(saashq.boot.allowed_modules, function (icon) {
			var m = icon.module_name;
			var type = saashq.modules[m] && saashq.modules[m].type;

			if (saashq.boot.user.allow_modules.indexOf(m) === -1) return null;

			var ret = null;
			if (type === "module") {
				if (saashq.boot.user.allow_modules.indexOf(m) != -1 || saashq.modules[m].is_help)
					ret = m;
			} else if (type === "page") {
				if (saashq.boot.allowed_pages.indexOf(saashq.modules[m].link) != -1) ret = m;
			} else if (type === "list") {
				if (saashq.model.can_read(saashq.modules[m]._doctype)) ret = m;
			} else if (type === "view") {
				ret = m;
			} else if (type === "setup") {
				if (
					saashq.user.has_role("System Manager") ||
					saashq.user.has_role("Administrator")
				)
					ret = m;
			} else {
				ret = m;
			}

			return ret;
		});

		return modules_list;
	},

	is_report_manager: function () {
		return saashq.user.has_role(["Administrator", "System Manager", "Report Manager"]);
	},

	get_formatted_email: function (email) {
		var fullname = saashq.user.full_name(email);

		if (!fullname) {
			return email;
		} else {
			// to quote or to not
			var quote = "";

			// only if these special characters are found
			// why? To make the output same as that in python!
			if (fullname.search(/[\[\]\\()<>@,:;".]/) !== -1) {
				quote = '"';
			}

			return repl("%(quote)s%(fullname)s%(quote)s <%(email)s>", {
				fullname: fullname,
				email: email,
				quote: quote,
			});
		}
	},

	get_emails: () => {
		return Object.keys(saashq.boot.user_info).map((key) => saashq.boot.user_info[key].email);
	},

	/* Normally saashq.user is an object
	 * having properties and methods.
	 * But in the following case
	 *
	 * if (saashq.user === 'Administrator')
	 *
	 * saashq.user will cast to a string
	 * returning saashq.user.name
	 */
	toString: function () {
		return this.name;
	},
});

saashq.session_alive = true;
$(document).bind("mousemove", function () {
	if (saashq.session_alive === false) {
		$(document).trigger("session_alive");
	}
	saashq.session_alive = true;
	if (saashq.session_alive_timeout) clearTimeout(saashq.session_alive_timeout);
	saashq.session_alive_timeout = setTimeout("saashq.session_alive=false;", 30000);
});
