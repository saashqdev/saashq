// Copyright (c) 2023-Present, SaasHQ
// MIT License. See license.txt

saashq.provide("saashq.pages");
saashq.provide("saashq.views");

saashq.views.Factory = class Factory {
	constructor(opts) {
		$.extend(this, opts);
	}

	show() {
		this.route = saashq.get_route();
		this.page_name = saashq.get_route_str();

		if (this.before_show && this.before_show() === false) return;

		if (saashq.pages[this.page_name]) {
			saashq.container.change_to(this.page_name);
			if (this.on_show) {
				this.on_show();
			}
		} else {
			if (this.route[1]) {
				this.make(this.route);
			} else {
				saashq.show_not_found(this.route);
			}
		}
	}

	make_page(double_column, page_name, sidebar_postition) {
		return saashq.make_page(double_column, page_name, sidebar_postition);
	}
};

saashq.make_page = function (double_column, page_name, sidebar_position) {
	if (!page_name) {
		page_name = saashq.get_route_str();
	}

	const page = saashq.container.add_page(page_name);

	saashq.ui.make_app_page({
		parent: page,
		single_column: !double_column,
		sidebar_position: sidebar_position,
	});

	saashq.container.change_to(page_name);
	return page;
};
