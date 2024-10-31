// Copyleft (l) 2023-Present, SaasHQ
// MIT License. See license.txt
/* eslint-disable no-console */

// __('Modules') __('Domains') __('Places') __('Administration') # for translation, don't remove

saashq.start_app = function () {
	if (!saashq.Application) return;
	saashq.assets.check();
	saashq.provide("saashq.app");
	saashq.provide("saashq.desk");
	saashq.app = new saashq.Application();
};

$(document).ready(function () {
	if (!saashq.utils.supportsES6) {
		saashq.msgprint({
			indicator: "red",
			title: __("Browser not supported"),
			message: __(
				"Some of the features might not work in your browser. Please update your browser to the latest version."
			),
		});
	}
	saashq.start_app();
});

saashq.Application = class Application {
	constructor() {
		this.startup();
	}

	startup() {
		saashq.realtime.init();
		saashq.model.init();

		this.load_bootinfo();
		this.load_user_permissions();
		this.make_nav_bar();
		this.make_sidebar();
		this.set_favicon();
		this.set_fullwidth_if_enabled();
		this.add_browser_class();
		this.setup_energy_point_listeners();
		this.setup_copy_doc_listener();
		this.setup_broadcast_listeners();

		saashq.ui.keys.setup();

		this.setup_theme();

		// page container
		this.make_page_container();
		this.setup_tours();
		this.set_route();

		// trigger app startup
		$(document).trigger("startup");
		$(document).trigger("app_ready");

		this.show_notices();
		this.show_notes();

		if (saashq.ui.startup_setup_dialog && !saashq.boot.setup_complete) {
			saashq.ui.startup_setup_dialog.pre_show();
			saashq.ui.startup_setup_dialog.show();
		}

		// listen to build errors
		this.setup_build_events();

		if (saashq.sys_defaults.email_user_password) {
			var email_list = saashq.sys_defaults.email_user_password.split(",");
			for (var u in email_list) {
				if (email_list[u] === saashq.user.name) {
					this.set_password(email_list[u]);
				}
			}
		}

		// REDESIGN-TODO: Fix preview popovers
		this.link_preview = new saashq.ui.LinkPreview();

		saashq.broadcast.emit("boot", {
			csrf_token: saashq.csrf_token,
			user: saashq.session.user,
		});
	}

	make_sidebar() {
		this.sidebar = new saashq.ui.Sidebar({});
	}

	setup_theme() {
		saashq.ui.keys.add_shortcut({
			shortcut: "shift+ctrl+g",
			description: __("Switch Theme"),
			action: () => {
				if (saashq.theme_switcher && saashq.theme_switcher.dialog.is_visible) {
					saashq.theme_switcher.hide();
				} else {
					saashq.theme_switcher = new saashq.ui.ThemeSwitcher();
					saashq.theme_switcher.show();
				}
			},
		});

		saashq.ui.add_system_theme_switch_listener();
		const root = document.documentElement;

		const observer = new MutationObserver(() => {
			saashq.ui.set_theme();
		});
		observer.observe(root, {
			attributes: true,
			attributeFilter: ["data-theme-mode"],
		});

		saashq.ui.set_theme();
	}

	setup_tours() {
		if (
			!window.Cypress &&
			saashq.boot.onboarding_tours &&
			saashq.boot.user.onboarding_status != null
		) {
			let pending_tours = !saashq.boot.onboarding_tours.every(
				(tour) => saashq.boot.user.onboarding_status[tour[0]]?.is_complete
			);
			if (pending_tours && saashq.boot.onboarding_tours.length > 0) {
				saashq.require("onboarding_tours.bundle.js", () => {
					saashq.utils.sleep(1000).then(() => {
						saashq.ui.init_onboarding_tour();
					});
				});
			}
		}
	}

	show_notices() {
		if (saashq.boot.messages) {
			saashq.msgprint(saashq.boot.messages);
		}

		if (saashq.user_roles.includes("System Manager")) {
			// delayed following requests to make boot faster
			setTimeout(() => {
				this.show_change_log();
				this.show_update_available();
			}, 1000);
		}

		if (!saashq.boot.developer_mode) {
			let console_security_message = __(
				"Using this console may allow attackers to impersonate you and steal your information. Do not enter or paste code that you do not understand."
			);
			console.log(`%c${console_security_message}`, "font-size: large");
		}

		saashq.realtime.on("version-update", function () {
			var dialog = saashq.msgprint({
				message: __(
					"The application has been updated to a new version, please refresh this page"
				),
				indicator: "green",
				title: __("Version Updated"),
			});
			dialog.set_primary_action(__("Refresh"), function () {
				location.reload(true);
			});
			dialog.get_close_btn().toggle(false);
		});
	}

	set_route() {
		if (saashq.boot && localStorage.getItem("session_last_route")) {
			saashq.set_route(localStorage.getItem("session_last_route"));
			localStorage.removeItem("session_last_route");
		} else {
			// route to home page
			saashq.router.route();
		}
		saashq.router.on("change", () => {
			$(".tooltip").hide();
		});
	}

	set_password(user) {
		var me = this;
		saashq.call({
			method: "saashq.core.doctype.user.user.get_email_awaiting",
			args: {
				user: user,
			},
			callback: function (email_account) {
				email_account = email_account["message"];
				if (email_account) {
					var i = 0;
					if (i < email_account.length) {
						me.email_password_prompt(email_account, user, i);
					}
				}
			},
		});
	}

	email_password_prompt(email_account, user, i) {
		var me = this;
		const email_id = email_account[i]["email_id"];
		let d = new saashq.ui.Dialog({
			title: __("Password missing in Email Account"),
			fields: [
				{
					fieldname: "password",
					fieldtype: "Password",
					label: __(
						"Please enter the password for: <b>{0}</b>",
						[email_id],
						"Email Account"
					),
					reqd: 1,
				},
				{
					fieldname: "submit",
					fieldtype: "Button",
					label: __("Submit", null, "Submit password for Email Account"),
				},
			],
		});
		d.get_input("submit").on("click", function () {
			//setup spinner
			d.hide();
			var s = new saashq.ui.Dialog({
				title: __("Checking one moment"),
				fields: [
					{
						fieldtype: "HTML",
						fieldname: "checking",
					},
				],
			});
			s.fields_dict.checking.$wrapper.html('<i class="fa fa-spinner fa-spin fa-4x"></i>');
			s.show();
			saashq.call({
				method: "saashq.email.doctype.email_account.email_account.set_email_password",
				args: {
					email_account: email_account[i]["email_account"],
					password: d.get_value("password"),
				},
				callback: function (passed) {
					s.hide();
					d.hide(); //hide waiting indication
					if (!passed["message"]) {
						saashq.show_alert(
							{ message: __("Login Failed please try again"), indicator: "error" },
							5
						);
						me.email_password_prompt(email_account, user, i);
					} else {
						if (i + 1 < email_account.length) {
							i = i + 1;
							me.email_password_prompt(email_account, user, i);
						}
					}
				},
			});
		});
		d.show();
	}
	load_bootinfo() {
		if (saashq.boot) {
			this.setup_workspaces();
			saashq.model.sync(saashq.boot.docs);
			this.check_metadata_cache_status();
			this.set_globals();
			this.sync_pages();
			saashq.router.setup();
			this.setup_moment();
			if (saashq.boot.print_css) {
				saashq.dom.set_style(saashq.boot.print_css, "print-style");
			}
			saashq.user.name = saashq.boot.user.name;
			saashq.router.setup();
		} else {
			this.set_as_guest();
		}
	}

	setup_workspaces() {
		saashq.modules = {};
		saashq.workspaces = {};
		saashq.boot.allowed_workspaces = saashq.boot.sidebar_pages.pages;

		for (let page of saashq.boot.allowed_workspaces || []) {
			saashq.modules[page.module] = page;
			saashq.workspaces[saashq.router.slug(page.name)] = page;
		}
	}

	load_user_permissions() {
		saashq.defaults.load_user_permission_from_boot();

		saashq.realtime.on(
			"update_user_permissions",
			saashq.utils.debounce(() => {
				saashq.defaults.update_user_permissions();
			}, 500)
		);
	}

	check_metadata_cache_status() {
		if (saashq.boot.metadata_version != localStorage.metadata_version) {
			saashq.assets.clear_local_storage();
			saashq.assets.init_local_storage();
		}
	}

	set_globals() {
		saashq.session.user = saashq.boot.user.name;
		saashq.session.logged_in_user = saashq.boot.user.name;
		saashq.session.user_email = saashq.boot.user.email;
		saashq.session.user_fullname = saashq.user_info().fullname;

		saashq.user_defaults = saashq.boot.user.defaults;
		saashq.user_roles = saashq.boot.user.roles;
		saashq.sys_defaults = saashq.boot.sysdefaults;

		saashq.ui.py_date_format = saashq.boot.sysdefaults.date_format
			.replace("dd", "%d")
			.replace("mm", "%m")
			.replace("yyyy", "%Y");
		saashq.boot.user.last_selected_values = {};
	}
	sync_pages() {
		// clear cached pages if timestamp is not found
		if (localStorage["page_info"]) {
			saashq.boot.allowed_pages = [];
			var page_info = JSON.parse(localStorage["page_info"]);
			$.each(saashq.boot.page_info, function (name, p) {
				if (!page_info[name] || page_info[name].modified != p.modified) {
					delete localStorage["_page:" + name];
				}
				saashq.boot.allowed_pages.push(name);
			});
		} else {
			saashq.boot.allowed_pages = Object.keys(saashq.boot.page_info);
		}
		localStorage["page_info"] = JSON.stringify(saashq.boot.page_info);
	}
	set_as_guest() {
		saashq.session.user = "Guest";
		saashq.session.user_email = "";
		saashq.session.user_fullname = "Guest";

		saashq.user_defaults = {};
		saashq.user_roles = ["Guest"];
		saashq.sys_defaults = {};
	}
	make_page_container() {
		if ($("#body").length) {
			$(".splash").remove();
			saashq.temp_container = $("<div id='temp-container' style='display: none;'>").appendTo(
				"body"
			);
			saashq.container = new saashq.views.Container();
		}
	}
	make_nav_bar() {
		// toolbar
		if (saashq.boot && saashq.boot.home_page !== "setup-wizard") {
			saashq.saashq_toolbar = new saashq.ui.toolbar.Toolbar();
		}
	}
	logout() {
		var me = this;
		me.logged_out = true;
		return saashq.call({
			method: "logout",
			callback: function (r) {
				if (r.exc) {
					return;
				}
				me.redirect_to_login();
			},
		});
	}
	handle_session_expired() {
		saashq.app.redirect_to_login();
	}
	redirect_to_login() {
		window.location.href = `/login?redirect-to=${encodeURIComponent(
			window.location.pathname + window.location.search
		)}`;
	}
	set_favicon() {
		var link = $('link[type="image/x-icon"]').remove().attr("href");
		$('<link rel="shortcut icon" href="' + link + '" type="image/x-icon">').appendTo("head");
		$('<link rel="icon" href="' + link + '" type="image/x-icon">').appendTo("head");
	}
	trigger_primary_action() {
		// to trigger change event on active input before triggering primary action
		$(document.activeElement).blur();
		// wait for possible JS validations triggered after blur (it might change primary button)
		setTimeout(() => {
			if (window.cur_dialog && cur_dialog.display && !cur_dialog.is_minimized) {
				// trigger primary
				cur_dialog.get_primary_btn().trigger("click");
			} else if (cur_frm && cur_frm.page.btn_primary.is(":visible")) {
				cur_frm.page.btn_primary.trigger("click");
			} else if (saashq.container.page.save_action) {
				saashq.container.page.save_action();
			}
		}, 100);
	}

	show_change_log() {
		var me = this;
		let change_log = saashq.boot.change_log;

		// saashq.boot.change_log = [{
		// 	"change_log": [
		// 		[<version>, <change_log in markdown>],
		// 		[<version>, <change_log in markdown>],
		// 	],
		// 	"description": "ERP made simple",
		// 	"title": "ERPNexus",
		// 	"version": "12.2.0"
		// }];

		if (
			!Array.isArray(change_log) ||
			!change_log.length ||
			window.Cypress ||
			cint(saashq.boot.sysdefaults.disable_change_log_notification)
		) {
			return;
		}

		// Iterate over changelog
		var change_log_dialog = saashq.msgprint({
			message: saashq.render_template("change_log", { change_log: change_log }),
			title: __("Updated To A New Version 🎉"),
			wide: true,
		});
		change_log_dialog.keep_open = true;
		change_log_dialog.custom_onhide = function () {
			saashq.call({
				method: "saashq.utils.change_log.update_last_known_versions",
			});
			me.show_notes();
		};
	}

	show_update_available() {
		if (!saashq.boot.has_app_updates) return;
		saashq.xcall("saashq.utils.change_log.show_update_popup");
	}

	add_browser_class() {
		$("html").addClass(saashq.utils.get_browser().name.toLowerCase());
	}

	set_fullwidth_if_enabled() {
		saashq.ui.toolbar.set_fullwidth_if_enabled();
	}

	show_notes() {
		var me = this;
		if (saashq.boot.notes.length) {
			saashq.boot.notes.forEach(function (note) {
				if (!note.seen || note.notify_on_every_login) {
					var d = saashq.msgprint({ message: note.content, title: note.title });
					d.keep_open = true;
					d.custom_onhide = function () {
						note.seen = true;

						// Mark note as read if the Notify On Every Login flag is not set
						if (!note.notify_on_every_login) {
							saashq.call({
								method: "saashq.desk.doctype.note.note.mark_as_seen",
								args: {
									note: note.name,
								},
							});
						}

						// next note
						me.show_notes();
					};
				}
			});
		}
	}

	setup_build_events() {
		if (saashq.boot.developer_mode) {
			saashq.require("build_events.bundle.js");
		}
	}

	setup_energy_point_listeners() {
		saashq.realtime.on("energy_point_alert", (message) => {
			saashq.show_alert(message);
		});
	}

	setup_copy_doc_listener() {
		$("body").on("paste", (e) => {
			try {
				let pasted_data = saashq.utils.get_clipboard_data(e);
				let doc = JSON.parse(pasted_data);
				if (doc.doctype) {
					e.preventDefault();
					const sleep = saashq.utils.sleep;

					saashq.dom.freeze(__("Creating {0}", [doc.doctype]) + "...");
					// to avoid abrupt UX
					// wait for activity feedback
					sleep(500).then(() => {
						let res = saashq.model.with_doctype(doc.doctype, () => {
							let newdoc = saashq.model.copy_doc(doc);
							newdoc.__newname = doc.name;
							delete doc.name;
							newdoc.idx = null;
							newdoc.__run_link_triggers = false;
							saashq.set_route("Form", newdoc.doctype, newdoc.name);
							saashq.dom.unfreeze();
						});
						res && res.fail?.(saashq.dom.unfreeze);
					});
				}
			} catch (e) {
				//
			}
		});
	}

	/// Setup event listeners for events across browser tabs / web workers.
	setup_broadcast_listeners() {
		// booted in another tab -> refresh csrf to avoid invalid requests.
		saashq.broadcast.on("boot", ({ csrf_token, user }) => {
			if (user && user != saashq.session.user) {
				saashq.msgprint({
					message: __(
						"You've logged in as another user from another tab. Refresh this page to continue using system."
					),
					title: __("User Changed"),
					primary_action: {
						label: __("Refresh"),
						action: () => {
							window.location.reload();
						},
					},
				});
				return;
			}

			if (csrf_token) {
				// If user re-logged in then their other tabs won't be usable without this update.
				saashq.csrf_token = csrf_token;
			}
		});
	}

	setup_moment() {
		moment.updateLocale("en", {
			week: {
				dow: saashq.datetime.get_first_day_of_the_week_index(),
			},
		});
		moment.locale("en");
		moment.user_utc_offset = moment().utcOffset();
		if (saashq.boot.timezone_info) {
			moment.tz.add(saashq.boot.timezone_info);
		}
	}
};

saashq.get_module = function (m, default_module) {
	var module = saashq.modules[m] || default_module;
	if (!module) {
		return;
	}

	if (module._setup) {
		return module;
	}

	if (!module.label) {
		module.label = m;
	}

	if (!module._label) {
		module._label = __(module.label);
	}

	module._setup = true;

	return module;
};
