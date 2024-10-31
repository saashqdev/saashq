saashq.ui.form.ControlMultiCheck = class ControlMultiCheck extends saashq.ui.form.Control {
	// UI: multiple checkboxes
	// Value: Array of values
	// Options: Array of label/value/checked option objects

	make() {
		super.make();
		if (this.df.label) {
			this.$label = $(`<label class="control-label">${this.df.label}</label>`).appendTo(
				this.wrapper
			);
		}
		this.$load_state = $(`<div class="load-state text-muted small">${__("Loading")}...</div>`);
		this.$select_buttons = this.get_select_buttons().appendTo(this.wrapper);
		this.$load_state.appendTo(this.wrapper);

		// In your implementation, you may use the 'columns' property to specify either of:
		// - minimum column width, e.g. `"15rem"`
		// - fixed number of columns, e.g. `3`
		// - both minimum column width and maximum number of columns, e.g. `"15rem 5"`
		const columns = this.df.columns;
		this.$checkbox_area = $('<div class="checkbox-options"></div>').appendTo(this.wrapper);
		this.$checkbox_area.get(0).style.setProperty("--checkbox-options-columns", columns);
	}

	refresh() {
		this.set_options();
		this.bind_checkboxes();
		super.refresh();
	}

	refresh_input() {
		this.select_options(this.selected_options);
	}

	set_options() {
		this.$load_state.show();
		this.$select_buttons.hide();
		this.parse_df_options();

		if (this.df.get_data) {
			if (typeof this.df.get_data().then == "function") {
				this.df.get_data().then((results) => {
					this.options = results;
					this.make_checkboxes();
				});
			} else {
				this.options = this.df.get_data();
				this.make_checkboxes();
			}
		} else {
			this.make_checkboxes();
		}
	}

	parse_df_options() {
		if (Array.isArray(this.df.options)) {
			this.options = this.df.options;
		} else if (
			this.df.options &&
			this.df.options.length > 0 &&
			saashq.utils.is_json(this.df.options)
		) {
			let args = JSON.parse(this.df.options);
			if (Array.isArray(args)) {
				this.options = args;
			} else if (Array.isArray(args.options)) {
				this.options = args.options;
			}
		} else {
			this.options = [];
		}
	}

	make_checkboxes() {
		this.$load_state.hide();
		this.$checkbox_area.empty();
		if (this.df.sort_options != false) {
			// Sort if sort_options is undefined, null or truthy.
			this.options.sort((a, b) => cstr(a.label).localeCompare(cstr(b.label)));
		}
		this.options.forEach((option) => {
			let checkbox = this.get_checkbox_element(option).appendTo(this.$checkbox_area);
			if (option.danger) {
				checkbox.find(".label-area").addClass("text-danger");
			}
			option.$checkbox = checkbox;
		});
		if (this.df.select_all) {
			this.setup_select_all();
		}
		this.set_checked_options();
	}

	bind_checkboxes() {
		$(this.wrapper).on("change", ":checkbox", (e) => {
			const $checkbox = $(e.target);
			const option_name = $checkbox.attr("data-unit");
			if ($checkbox.is(":checked")) {
				if (this.selected_options.includes(option_name)) return;
				this.selected_options.push(option_name);
			} else {
				let index = this.selected_options.indexOf(option_name);
				if (index > -1) {
					this.selected_options.splice(index, 1);
				}
			}
			this.df.on_change && this.df.on_change();
		});
	}

	set_checked_options() {
		this.selected_options = this.options.filter((o) => o.checked).map((o) => o.value);
		this.select_options(this.selected_options);
	}

	setup_select_all() {
		this.$select_buttons.show();
		this.$select_buttons.find(".select-all").on("click", () => {
			this.select_all();
		});
		this.$select_buttons.find(".deselect-all").on("click", () => {
			this.select_all(true);
		});
	}

	select_all(deselect = false) {
		$(this.wrapper).find(`:checkbox`).prop("checked", deselect).trigger("click");
	}

	select_options(selected_options) {
		this.options
			.map((option) => option.value)
			.forEach((value) => {
				let $checkbox = $(this.wrapper).find(`:checkbox[data-unit="${value}"]`)[0];
				if ($checkbox) $checkbox.checked = selected_options.includes(value);
			});
	}

	get_value() {
		return this.selected_options;
	}

	get_checked_options() {
		return this.get_value();
	}

	get_unchecked_options() {
		return this.options
			.map((o) => o.value)
			.filter((value) => !this.selected_options.includes(value));
	}

	get_checkbox_element(option) {
		return $(`
			<div class="checkbox unit-checkbox">
				<label title="${option.description || ""}">
					<input type="checkbox" data-unit="${option.value}"></input>
					<span class="label-area" data-unit="${option.value}">${option.label}</span>
				</label>
			</div>
		`);
	}

	get_select_buttons() {
		return $(`
		<div class="bulk-select-options">
			<button class="btn btn-xs btn-default select-all">
				${__("Select All")}
			</button>
			<button class="btn btn-xs btn-default deselect-all">
				${__("Unselect All")}
			</button>
		</div>
		`);
	}
};
