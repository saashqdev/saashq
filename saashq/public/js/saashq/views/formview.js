// Copyleft (l) 2023-Present, SaasHQ
// MIT License. See license.txt

saashq.provide("saashq.views.formview");

saashq.views.FormFactory = class FormFactory extends saashq.views.Factory {
	make(route) {
		var doctype = route[1],
			doctype_layout = saashq.router.doctype_layout || doctype;

		if (!saashq.views.formview[doctype_layout]) {
			saashq.model.with_doctype(doctype, () => {
				this.page = saashq.container.add_page(doctype_layout);
				saashq.views.formview[doctype_layout] = this.page;
				this.make_and_show(doctype, route);
			});
		} else {
			this.show_doc(route);
		}

		this.setup_events();
	}

	make_and_show(doctype, route) {
		if (saashq.router.doctype_layout) {
			saashq.model.with_doc("DocType Layout", saashq.router.doctype_layout, () => {
				this.make_form(doctype);
				this.show_doc(route);
			});
		} else {
			this.make_form(doctype);
			this.show_doc(route);
		}
	}

	make_form(doctype) {
		this.page.frm = new saashq.ui.form.Form(
			doctype,
			this.page,
			true,
			saashq.router.doctype_layout
		);
	}

	setup_events() {
		if (!this.initialized) {
			$(document).on("page-change", function () {
				saashq.ui.form.close_grid_form();
			});
		}
		this.initialized = true;
	}

	show_doc(route) {
		var doctype = route[1],
			doctype_layout = saashq.router.doctype_layout || doctype,
			name = route.slice(2).join("/");

		if (saashq.model.new_names[name]) {
			// document has been renamed, reroute
			name = saashq.model.new_names[name];
			saashq.set_route("Form", doctype_layout, name);
			return;
		}

		const doc = saashq.get_doc(doctype, name);
		if (
			doc &&
			saashq.model.get_docinfo(doctype, name) &&
			(doc.__islocal || saashq.model.is_fresh(doc))
		) {
			// is document available and recent?
			this.render(doctype_layout, name);
		} else {
			this.fetch_and_render(doctype, name, doctype_layout);
		}
	}

	fetch_and_render(doctype, name, doctype_layout) {
		saashq.model.with_doc(doctype, name, (name, r) => {
			if (r && r["403"]) return; // not permitted

			if (!(locals[doctype] && locals[doctype][name])) {
				if (name && name.substr(0, 3) === "new") {
					this.render_new_doc(doctype, name, doctype_layout);
				} else {
					saashq.show_not_found();
				}
				return;
			}
			this.render(doctype_layout, name);
		});
	}

	render_new_doc(doctype, name, doctype_layout) {
		const new_name = saashq.model.make_new_doc_and_get_name(doctype, true);
		if (new_name === name) {
			this.render(doctype_layout, name);
		} else {
			saashq.route_flags.replace_route = true;
			saashq.set_route("Form", doctype_layout, new_name);
		}
	}

	render(doctype_layout, name) {
		saashq.container.change_to(doctype_layout);
		saashq.views.formview[doctype_layout].frm.refresh(name);
	}
};
