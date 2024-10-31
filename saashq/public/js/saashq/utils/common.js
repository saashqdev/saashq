// common file between desk and website
import md5 from "md5";

saashq.avatar = function (
	user,
	css_class,
	title,
	image_url = null,
	remove_color = false,
	filterable = false
) {
	let user_info;
	if (user) {
		// desk
		user_info = saashq.user_info(user);
	} else {
		// website
		let full_name = title || saashq.get_cookie("full_name");
		user_info = {
			image: image_url === null ? saashq.get_cookie("user_image") : image_url,
			fullname: full_name,
			abbr: saashq.get_abbr(full_name),
			color: saashq.get_palette(full_name),
		};
	}

	if (!title) {
		title = user_info.fullname;
	}

	let data_attr = "";
	if (filterable) {
		css_class += " filterable";
		data_attr = `data-filter="_assign,like,%${user}%"`;
	}

	return saashq.get_avatar(
		css_class,
		title,
		image_url || user_info.image,
		remove_color,
		data_attr
	);
};

saashq.get_avatar = function (css_class, title, image_url = null, remove_color, data_attributes) {
	if (!css_class) {
		css_class = "avatar-small";
	}
	let el = document.createElement("div");

	if (image_url) {
		el.innerHTML = `
			<span class="avatar ${css_class}" ${data_attributes}>
				<span class="avatar-frame" style='background-image: url("${image_url}")'</span>
			</span>`;
	} else {
		let abbr = saashq.get_abbr(title);
		let style = "";
		if (!remove_color) {
			let color = saashq.get_palette(title);
			style = `background-color: var(${color[0]}); color: var(${color[1]})`;
		}

		if (css_class === "avatar-small" || css_class == "avatar-xs") {
			abbr = abbr.substr(0, 1);
		}

		el.innerHTML = `<span class="avatar ${css_class}" ${data_attributes}>
			<div class="avatar-frame standard-image"
				style="${style}">
					${abbr}
			</div>
		</span>`;
	}

	el.querySelector(".avatar").setAttribute("title", title);
	el.querySelector(".avatar-frame").setAttribute("title", title);

	return el.innerHTML;
};

saashq.avatar_group = function (users, limit = 4, options = {}) {
	let avatar_action_html = "";
	const display_users = users.slice(0, limit);
	const extra_users = users.slice(limit);
	const css_class = options.css_class || "";

	let html = display_users
		.map((user) =>
			saashq.avatar(user, "avatar-small " + css_class, null, null, false, options.filterable)
		)
		.join("");
	if (extra_users.length === 1) {
		html += saashq.avatar(
			extra_users[0],
			"avatar-small " + css_class,
			null,
			null,
			false,
			options.filterable
		);
	} else if (extra_users.length > 1) {
		html = `
			${html}
			<span class="avatar avatar-small ${css_class}">
				<div class="avatar-frame standard-image avatar-extra-count"
					title="${extra_users.map((u) => saashq.user_info(u).fullname).join(", ")}">
					+${extra_users.length}
				</div>
			</span>
		`;
	}

	if (options.action_icon) {
		avatar_action_html = `
			<span class="avatar avatar-small">
				<div class="avatar-frame avatar-action">
					${saashq.utils.icon(options.action_icon, "sm")}
				</div>
			</span>
		`;
	}

	const $avatar_group = $(`<div class="avatar-group ${options.align || "right"} ${
		options.overlap != false ? "overlap" : ""
	}">
			${html}
			${avatar_action_html}
		</div>`);

	$avatar_group.find(".avatar-action").on("click", options.action);
	return $avatar_group;
};

saashq.ui.scroll = function (element, animate, additional_offset) {
	var header_offset = $(".navbar").height() + $(".page-head").height();
	var top = $(element).offset().top - header_offset - cint(additional_offset);
	if (animate) {
		$("html, body").animate({ scrollTop: top });
	} else {
		$(window).scrollTop(top);
	}
};

saashq.palette = [
	["--orange-avatar-bg", "--orange-avatar-color"],
	["--pink-avatar-bg", "--pink-avatar-color"],
	["--blue-avatar-bg", "--blue-avatar-color"],
	["--green-avatar-bg", "--green-avatar-color"],
	["--dark-green-avatar-bg", "--dark-green-avatar-color"],
	["--red-avatar-bg", "--red-avatar-color"],
	["--yellow-avatar-bg", "--yellow-avatar-color"],
	["--purple-avatar-bg", "--purple-avatar-color"],
	["--gray-avatar-bg", "--gray-avatar-color0"],
];

saashq.get_palette = function (txt) {
	if (!txt) return saashq.palette[8]; // breaks when undefined
	var idx = cint((parseInt(md5(txt).substr(4, 2), 16) + 1) / 5.33);
	return saashq.palette[idx % 8];
};

saashq.get_abbr = function (txt, max_length) {
	if (!txt) return "";
	var abbr = "";
	$.each(txt.split(" "), function (i, w) {
		if (abbr.length >= (max_length || 2)) {
			// break
			return false;
		} else if (!w.trim().length) {
			// continue
			return true;
		}
		abbr += w.trim()[0];
	});

	return abbr || "?";
};

saashq.gravatars = {};
saashq.get_gravatar = function (email_id, size = 0) {
	var param = size ? "s=" + size : "d=retro";
	if (!saashq.gravatars[email_id]) {
		// TODO: check if gravatar exists
		saashq.gravatars[email_id] =
			"https://secure.gravatar.com/avatar/" + md5(email_id) + "?" + param;
	}
	return saashq.gravatars[email_id];
};

// string commons

window.repl = function repl(s, dict) {
	if (s == null) return "";
	for (var key in dict) {
		s = s.split("%(" + key + ")s").join(dict[key]);
	}
	return s;
};

window.replace_all = function (s, t1, t2) {
	return s.split(t1).join(t2);
};

window.strip_html = function (txt) {
	return cstr(txt).replace(/<[^>]*>/g, "");
};

window.strip = function (s, chars) {
	if (s) {
		s = lstrip(s, chars);
		s = rstrip(s, chars);
		return s;
	}
};

window.lstrip = function lstrip(s, chars) {
	if (!chars) chars = ["\n", "\t", " "];
	// strip left
	let first_char = s.substr(0, 1);
	while (chars.includes(first_char)) {
		s = s.substr(1);
		first_char = s.substr(0, 1);
	}
	return s;
};

window.rstrip = function (s, chars) {
	if (!chars) chars = ["\n", "\t", " "];
	let last_char = s.substr(s.length - 1);
	while (chars.includes(last_char)) {
		s = s.substr(0, s.length - 1);
		last_char = s.substr(s.length - 1);
	}
	return s;
};

saashq.get_cookie = function getCookie(name) {
	return saashq.get_cookies()[name];
};

saashq.get_cookies = function getCookies() {
	var c = document.cookie,
		v = 0,
		cookies = {};
	if (document.cookie.match(/^\s*\$Version=(?:"1"|1);\s*(.*)/)) {
		c = RegExp.$1;
		v = 1;
	}
	if (v === 0) {
		c.split(/[,;]/).map(function (cookie) {
			var parts = cookie.split(/=/, 2),
				name = decodeURIComponent(parts[0].trimLeft()),
				value = parts.length > 1 ? decodeURIComponent(parts[1].trimRight()) : null;
			if (value && value.charAt(0) === '"') {
				value = value.substr(1, value.length - 2);
			}
			cookies[name] = value;
		});
	} else {
		c.match(
			/(?:^|\s+)([!#$%&'*+\-.0-9A-Z^`a-z|~]+)=([!#$%&'*+\-.0-9A-Z^`a-z|~]*|"(?:[\x20-\x7E\x80\xFF]|\\[\x00-\x7F])*")(?=\s*[,;]|$)/g
		).map(function ($0, $1) {
			var name = $0,
				value = $1.charAt(0) === '"' ? $1.substr(1, -1).replace(/\\(.)/g, "$1") : $1;
			cookies[name] = value;
		});
	}
	return cookies;
};

saashq.is_mobile = function () {
	return $(document).width() < 768;
};

saashq.is_large_screen = function () {
	return $(document).height() > 1180;
};

saashq.utils.xss_sanitise = function (string, options) {
	// Reference - https://www.owasp.org/index.php/XSS_(Cross_Site_Scripting)_Prevention_Cheat_Sheet
	let sanitised = string; // un-sanitised string.
	const DEFAULT_OPTIONS = {
		strategies: ["html", "js"], // use all strategies.
	};
	const HTML_ESCAPE_MAP = {
		"<": "&lt;",
		">": "&gt;",
		'"': "&quot;",
		"'": "&#x27;",
		"/": "&#x2F;",
	};
	const REGEX_SCRIPT = /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi; // used in jQuery 1.7.2 src/ajax.js Line 14
	const REGEX_ALERT = /confirm\(.*\)|alert\(.*\)|prompt\(.*\)/gi; // captures alert, confirm, prompt
	options = Object.assign({}, DEFAULT_OPTIONS, options); // don't deep copy, immutable beauty.

	// Rule 3 - TODO: Check event handlers?
	// script and alert should be checked first or else it will be escaped
	if (options.strategies.includes("js")) {
		sanitised = sanitised.replace(REGEX_SCRIPT, "");
		sanitised = sanitised.replace(REGEX_ALERT, "");
	}

	// Rule 1
	if (options.strategies.includes("html")) {
		for (let char in HTML_ESCAPE_MAP) {
			const escape = HTML_ESCAPE_MAP[char];
			const regex = new RegExp(char, "g");
			sanitised = sanitised.replace(regex, escape);
		}
	}

	return sanitised;
};

saashq.utils.sanitise_redirect = (url) => {
	const is_external = (() => {
		return (url) => {
			function domain(url) {
				let base_domain = /^(?:https?:\/\/)?(?:[^@\n]+@)?(?:www\.)?([^:/\n?]+)/gim.exec(
					url
				);
				return base_domain == null ? "" : base_domain[1];
			}

			function is_absolute(url) {
				// returns true for url that have a defined scheme
				// anything else, eg. internal urls return false
				return /^(?:[a-z]+:)?\/\//i.test(url);
			}

			// check for base domain only if the url is absolute
			// return true for relative url (except protocol-relative urls)
			return is_absolute(url) ? domain(location.href) !== domain(url) : false;
		};
	})();

	/*
	 * Strips out url containing the text `javascript` with or without any HTML Entities in it
	 **/
	const sanitise_javascript = (url) => {
		/*
		 * Written below split into parts, but actual is in one line regardless of whitespaces
		 * /
		 * 	j
		 * 		\s*(&#x.{1,7})?
		 * 	a
		 * 		\s*(&#x.{1,7})?
		 * 	v
		 * 		\s*(&#x.{1,7})?
		 * 	a
		 * 		\s*(&#x.{1,7})?
		 * 	s
		 * 		\s*(&#x.{1,7})?
		 * 	c
		 * 		\s*(&#x.{1,7})?
		 * 	r
		 * 		\s*(&#x.{1,7})?
		 * 	i
		 * 		\s*(&#x.{1,7})?
		 * 	p
		 * 		\s*(&#x.{1,7})?
		 * 	t
		 * /gi
		 * */
		const REGEX_ESC_UNIT = /\s*(&#x.{1,7})?/;
		const REGEX_SCRIPT = new RegExp(
			Array.from("javascript").join(REGEX_ESC_UNIT.source),
			"gi"
		);

		return url.replace(REGEX_SCRIPT, "");
	};

	url = saashq.utils.strip_url(url);

	return is_external(url)
		? ""
		: sanitise_javascript(saashq.utils.xss_sanitise(url, { strategies: ["js"] }));
};

saashq.utils.strip_url = (url) => {
	// strips invalid characters from the beginning of the URL
	// in our case, the url can start with either a protocol, //, or even #
	// so anything except those characters can be considered invalid
	return url.replace(/^[^A-Za-z0-9(//)#]+/g, "");
};

saashq.utils.new_auto_repeat_prompt = function (frm) {
	const fields = [
		{
			fieldname: "frequency",
			fieldtype: "Select",
			label: __("Frequency"),
			reqd: 1,
			options: [
				{ label: __("Daily"), value: "Daily" },
				{ label: __("Weekly"), value: "Weekly" },
				{ label: __("Monthly"), value: "Monthly" },
				{ label: __("Quarterly"), value: "Quarterly" },
				{ label: __("Half-yearly"), value: "Half-yearly" },
				{ label: __("Yearly"), value: "Yearly" },
			],
		},
		{
			fieldname: "start_date",
			fieldtype: "Date",
			label: __("Start Date"),
			reqd: 1,
			default: saashq.datetime.nowdate(),
		},
		{
			fieldname: "end_date",
			fieldtype: "Date",
			label: __("End Date"),
		},
	];
	saashq.prompt(
		fields,
		function (values) {
			saashq.call({
				method: "saashq.automation.doctype.auto_repeat.auto_repeat.make_auto_repeat",
				args: {
					doctype: frm.doc.doctype,
					docname: frm.doc.name,
					frequency: values["frequency"],
					start_date: values["start_date"],
					end_date: values["end_date"],
				},
				callback: function (r) {
					if (r.message) {
						saashq.show_alert({
							message: __("Auto Repeat created for this document"),
							indicator: "green",
						});
						frm.reload_doc();
					}
				},
			});
		},
		__("Auto Repeat"),
		__("Save")
	);
};

saashq.utils.get_page_view_count = function (route) {
	return saashq.call("saashq.website.doctype.web_page_view.web_page_view.get_page_view_count", {
		path: route,
	});
};
