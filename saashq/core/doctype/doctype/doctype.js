// Copyleft (l) 2023-Present, SaasHQ
// MIT License. See license.txt

saashq.ui.form.on("DocType", {
	onload: function (frm) {
		if (frm.is_new() && !frm.doc?.fields) {
			saashq.listview_settings["DocType"].new_doctype_dialog();
		}
		frm.call("check_pending_migration");
	},

	before_save: function (frm) {
		let form_builder = saashq.form_builder;
		if (form_builder?.store) {
			let fields = form_builder.store.update_fields();

			// if fields is a string, it means there is an error
			if (typeof fields === "string") {
				saashq.throw(fields);
			}
		}
	},

	after_save: function (frm) {
		if (
			saashq.form_builder &&
			saashq.form_builder.doctype === frm.doc.name &&
			saashq.form_builder.store
		) {
			saashq.form_builder.store.fetch();
		}
	},

	refresh: function (frm) {
		frm.set_query("role", "permissions", function (doc) {
			if (doc.custom && saashq.session.user != "Administrator") {
				return {
					query: "saashq.core.doctype.role.role.role_query",
					filters: [["Role", "name", "!=", "All"]],
				};
			}
		});

		if (saashq.session.user !== "Administrator" || !saashq.boot.developer_mode) {
			if (frm.is_new()) {
				frm.set_value("custom", 1);
			}
			frm.toggle_enable("custom", 0);
			frm.toggle_enable("is_virtual", 0);
			frm.toggle_enable("beta", 0);
		}

		if (!frm.is_new() && !frm.doc.istable) {
			const button_text = frm.doc.issingle
				? __("Go to {0}", [__(frm.doc.name)])
				: __("Go to {0} List", [__(frm.doc.name)]);
			frm.add_custom_button(button_text, () => {
				window.open(`/app/${saashq.router.slug(frm.doc.name)}`);
			});
		}

		const customize_form_link = `<a href="/app/customize-form">${__("Customize Form")}</a>`;
		if (!saashq.boot.developer_mode && !frm.doc.custom) {
			// make the document read-only
			frm.set_read_only();
			frm.dashboard.clear_comment();
			frm.dashboard.add_comment(
				__("DocTypes cannot be modified, please use {0} instead", [customize_form_link]),
				"blue",
				true
			);
		} else if (saashq.boot.developer_mode) {
			frm.dashboard.clear_comment();
			let msg = __(
				"This site is running in developer mode. Any change made here will be updated in code."
			);
			frm.dashboard.add_comment(msg, "yellow", true);
		}

		if (frm.is_new()) {
			frm.events.set_default_permission(frm);
			frm.set_value("default_view", "List");
		} else {
			frm.toggle_enable("engine", 0);
		}

		// set label for "In List View" for child tables
		frm.get_docfield("fields", "in_list_view").label = frm.doc.istable
			? __("In Grid View")
			: __("In List View");

		frm.cscript.autoname(frm);
		frm.cscript.set_naming_rule_description(frm);
		frm.trigger("setup_default_views");

		render_form_builder(frm);
	},

	istable: (frm) => {
		if (frm.doc.istable && frm.is_new()) {
			frm.set_value("default_view", null);
		} else if (!frm.doc.istable && !frm.is_new()) {
			frm.events.set_default_permission(frm);
		}
	},

	set_default_permission: (frm) => {
		if (!(frm.doc.permissions && frm.doc.permissions.length)) {
			frm.add_child("permissions", { role: "System Manager" });
		}
	},

	is_tree: (frm) => {
		frm.trigger("setup_default_views");
	},

	is_calendar_and_gantt: (frm) => {
		frm.trigger("setup_default_views");
	},

	setup_default_views: (frm) => {
		saashq.model.set_default_views_for_doctype(frm.doc.name, frm);
	},

	on_tab_change: (frm) => {
		let current_tab = frm.get_active_tab().label;

		if (current_tab === "Form") {
			frm.footer.wrapper.hide();
			frm.form_wrapper.find(".form-message").hide();
			frm.form_wrapper.addClass("mb-1");
		} else {
			frm.footer.wrapper.show();
			frm.form_wrapper.find(".form-message").show();
			frm.form_wrapper.removeClass("mb-1");
		}
	},
});

saashq.ui.form.on("DocField", {
	form_render(frm, doctype, docname) {
		frm.trigger("setup_fetch_from_fields", doctype, docname);
	},

	fieldtype: function (frm) {
		frm.trigger("max_attachments");
	},

	fields_add: (frm) => {
		frm.trigger("setup_default_views");
	},
});

function render_form_builder(frm) {
	if (saashq.form_builder && saashq.form_builder.doctype === frm.doc.name) {
		saashq.form_builder.setup_page_actions();
		saashq.form_builder.store.fetch();
		return;
	}

	if (saashq.form_builder) {
		saashq.form_builder.wrapper = $(frm.fields_dict["form_builder"].wrapper);
		saashq.form_builder.frm = frm;
		saashq.form_builder.doctype = frm.doc.name;
		saashq.form_builder.customize = false;
		saashq.form_builder.init(true);
		saashq.form_builder.store.fetch();
	} else {
		saashq.require("form_builder.bundle.js").then(() => {
			saashq.form_builder = new saashq.ui.FormBuilder({
				wrapper: $(frm.fields_dict["form_builder"].wrapper),
				frm: frm,
				doctype: frm.doc.name,
				customize: false,
			});
		});
	}
}

extend_cscript(cur_frm.cscript, new saashq.model.DocTypeController({ frm: cur_frm }));
