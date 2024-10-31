saashq.provide("saashq.ui");

export default class ListFilter {
	constructor({ wrapper, doctype }) {
		Object.assign(this, arguments[0]);
		this.can_add_global = saashq.user.has_role(["System Manager", "Administrator"]);
		this.filters = [];
		this.make();
		this.bind();
		this.refresh();
	}

	make() {
		// init dom
		this.wrapper.html(`
			<div class="input-area"></div>
			<div class="sidebar-action">
				<a class="saved-filters-preview">${__("Show Saved")}</a>
			</div>
			<div class="saved-filters"></div>
		`);

		this.$input_area = this.wrapper.find(".input-area");
		this.$list_filters = this.wrapper.find(".list-filters");
		this.$saved_filters = this.wrapper.find(".saved-filters").hide();
		this.$saved_filters_preview = this.wrapper.find(".saved-filters-preview");
		this.saved_filters_hidden = true;
		this.toggle_saved_filters(true);

		this.filter_input = saashq.ui.form.make_control({
			df: {
				fieldtype: "Data",
				placeholder: __("Filter Name"),
				input_class: "input-xs",
			},
			parent: this.$input_area,
			render_input: 1,
		});

		this.is_global_input = saashq.ui.form.make_control({
			df: {
				fieldtype: "Check",
				label: __("Is Global"),
			},
			parent: this.$input_area,
			render_input: 1,
		});
	}

	bind() {
		this.bind_save_filter();
		this.bind_toggle_saved_filters();
		this.bind_click_filter();
		this.bind_remove_filter();
	}

	refresh() {
		this.get_list_filters().then(() => {
			if (this.filters.length) {
				// expand collapsible sections
				this.wrapper.hasClass("hide") && this.section_title.trigger("click");
				this.$saved_filters_preview.show();
			} else {
				// hide collapsible sections
				!this.wrapper.hasClass("hide") && this.section_title.trigger("click");
				this.$saved_filters_preview.hide();
			}

			const html = this.filters.map((filter) => this.filter_template(filter));
			this.wrapper.find(".filter-pill").remove();
			this.$saved_filters.append(html);
		});
		this.is_global_input.toggle(false);
		this.filter_input.set_description("");
	}

	filter_template(filter) {
		return `<div class="list-link filter-pill list-sidebar-button btn btn-default" data-name="${
			filter.name
		}">
			<a class="ellipsis filter-name">${filter.filter_name}</a>
			<a class="remove">${saashq.utils.icon("close")}</a>
		</div>`;
	}

	bind_toggle_saved_filters() {
		this.wrapper.find(".saved-filters-preview").click(() => {
			this.toggle_saved_filters(this.saved_filters_hidden);
		});
	}

	toggle_saved_filters(show) {
		this.$saved_filters.toggle(show);
		const label = show ? __("Hide Saved") : __("Show Saved");
		this.wrapper.find(".saved-filters-preview").text(label);
		this.saved_filters_hidden = !this.saved_filters_hidden;
	}

	bind_click_filter() {
		this.wrapper.on("click", ".filter-pill .filter-name", (e) => {
			let $filter = $(e.currentTarget).parent(".filter-pill");
			this.set_applied_filter($filter);
			const name = $filter.attr("data-name");
			this.list_view.filter_area.clear().then(() => {
				this.list_view.filter_area.add(this.get_filters_values(name));
			});
		});
	}

	bind_remove_filter() {
		this.wrapper.on("click", ".filter-pill .remove", (e) => {
			const $li = $(e.currentTarget).closest(".filter-pill");
			const filter_label = $li.text().trim();

			saashq.confirm(
				__("Are you sure you want to remove the {0} filter?", [filter_label.bold()]),
				() => {
					const name = $li.attr("data-name");
					const applied_filters = this.get_filters_values(name);
					$li.remove();
					this.remove_filter(name).then(() => this.refresh());
					this.list_view.filter_area.remove_filters(applied_filters);
				}
			);
		});
	}

	bind_save_filter() {
		this.filter_input.$input.keydown(
			saashq.utils.debounce((e) => {
				const value = this.filter_input.get_value();
				const has_value = Boolean(value);

				if (e.which === saashq.ui.keyCode["ENTER"]) {
					if (!has_value || this.filter_name_exists(value)) return;

					this.filter_input.set_value("");
					this.save_filter(value).then(() => this.refresh());
					this.toggle_saved_filters(true);
				} else {
					let help_text = __("Press Enter to save");

					if (this.filter_name_exists(value)) {
						help_text = __("Duplicate Filter Name");
					}

					this.filter_input.set_description(has_value ? help_text : "");

					if (this.can_add_global) {
						this.is_global_input.toggle(has_value);
					}
				}
			}, 300)
		);
	}

	save_filter(filter_name) {
		return saashq.db.insert({
			doctype: "List Filter",
			reference_doctype: this.list_view.doctype,
			filter_name,
			for_user: this.is_global_input.get_value() ? "" : saashq.session.user,
			filters: JSON.stringify(this.get_current_filters()),
		});
	}

	remove_filter(name) {
		if (!name) return;
		return saashq.db.delete_doc("List Filter", name);
	}

	get_filters_values(name) {
		const filter = this.filters.find((filter) => filter.name === name);
		return JSON.parse(filter.filters || "[]");
	}

	get_current_filters() {
		return this.list_view.filter_area.get();
	}

	filter_name_exists(filter_name) {
		return (this.filters || []).find((f) => f.filter_name === filter_name);
	}

	get_list_filters() {
		if (saashq.session.user === "Guest") return Promise.resolve();
		return saashq.db
			.get_list("List Filter", {
				fields: ["name", "filter_name", "for_user", "filters"],
				filters: { reference_doctype: this.list_view.doctype },
				or_filters: [
					["for_user", "=", saashq.session.user],
					["for_user", "=", ""],
				],
				order_by: "filter_name asc",
			})
			.then((filters) => {
				this.filters = filters || [];
			});
	}

	set_applied_filter($filter) {
		this.$saved_filters
			.find(".btn-primary-light")
			.toggleClass("btn-primary-light btn-default");
		$filter.toggleClass("btn-default btn-primary-light");
	}
}
