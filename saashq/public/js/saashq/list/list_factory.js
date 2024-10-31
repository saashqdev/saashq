// Copyleft (l) 2023-Present, SaasHQ
// MIT License. See license.txt

saashq.provide("saashq.views.list_view");

window.cur_list = null;
saashq.views.ListFactory = class ListFactory extends saashq.views.Factory {
	make(route) {
		const me = this;
		const doctype = route[1];

		// List / Gantt / Kanban / etc
		let view_name = saashq.utils.to_title_case(route[2] || "List");

		// File is a special view
		if (doctype == "File" && !["Report", "Dashboard"].includes(view_name)) {
			view_name = "File";
		}

		let view_class = saashq.views[view_name + "View"];
		if (!view_class) view_class = saashq.views.ListView;

		if (view_class && view_class.load_last_view && view_class.load_last_view()) {
			// view can have custom routing logic
			return;
		}

		saashq.provide("saashq.views.list_view." + doctype);

		saashq.views.list_view[me.page_name] = new view_class({
			doctype: doctype,
			parent: me.make_page(true, me.page_name, "Right"),
		});

		me.set_cur_list();
	}

	before_show() {
		if (this.re_route_to_view()) {
			return false;
		}

		this.set_module_breadcrumb();
	}

	on_show() {
		this.set_cur_list();
		if (cur_list) cur_list.show();
	}

	re_route_to_view() {
		const doctype = this.route[1];
		const last_route = saashq.route_history.slice(-2)[0];
		if (
			this.route[0] === "List" &&
			this.route.length === 2 &&
			saashq.views.list_view[doctype] &&
			last_route &&
			last_route[0] === "List" &&
			last_route[1] === doctype
		) {
			// last route same as this route, so going back.
			// this happens because /app/List/Item will redirect to /app/List/Item/List
			// while coming from back button, the last 2 routes will be same, so
			// we know user is coming in the reverse direction (via back button)

			// example:
			// Step 1: /app/List/Item redirects to /app/List/Item/List
			// Step 2: User hits "back" comes back to /app/List/Item
			// Step 3: Now we cannot send the user back to /app/List/Item/List so go back one more step
			window.history.go(-1);
			return true;
		}
	}

	set_module_breadcrumb() {
		if (saashq.route_history.length > 1) {
			const prev_route = saashq.route_history[saashq.route_history.length - 2];
			if (prev_route[0] === "modules") {
				const doctype = this.route[1],
					module = prev_route[1];
				if (saashq.module_links[module] && saashq.module_links[module].includes(doctype)) {
					// save the last page from the breadcrumb was accessed
					saashq.breadcrumbs.set_doctype_module(doctype, module);
				}
			}
		}
	}

	set_cur_list() {
		cur_list = saashq.views.list_view[this.page_name];
		if (cur_list && cur_list.doctype !== this.route[1]) {
			// changing...
			window.cur_list = null;
		}
	}
};
