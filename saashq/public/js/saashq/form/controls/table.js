import Grid from "../grid";

saashq.ui.form.ControlTable = class ControlTable extends saashq.ui.form.Control {
	make() {
		super.make();

		// add title if prev field is not column / section heading or html
		this.grid = new Grid({
			frm: this.frm,
			df: this.df,
			parent: this.wrapper,
			control: this,
		});

		if (this.frm) {
			this.frm.grids[this.frm.grids.length] = this;
		}

		this.$wrapper.on("paste", ":text", (e) => {
			const table_field = this.df.fieldname;
			const grid = this.grid;
			const grid_pagination = grid.grid_pagination;
			const grid_rows = grid.grid_rows;
			const doctype = grid.doctype;
			const row_docname = $(e.target).closest(".grid-row").data("name");
			const in_grid_form = $(e.target).closest(".form-in-grid").length;
			const value_formatter_map = {
				Date: (val) => (val ? saashq.datetime.user_to_str(val) : val),
				Int: (val) => cint(val),
				Check: (val) => cint(val),
				Float: (val) => flt(val),
				Currency: (val) => flt(val),
			};

			let pasted_data = saashq.utils.get_clipboard_data(e);

			if (!pasted_data || in_grid_form) return;

			let data = saashq.utils.csv_to_array(pasted_data, "\t");

			if (data.length === 1 && data[0].length === 1) return;

			let fieldnames = [];
			let fieldtypes = [];
			// for raw data with column header
			if (this.get_field(data[0][0])) {
				data[0].forEach((column) => {
					fieldnames.push(this.get_field(column));
					const df = saashq.meta.get_docfield(doctype, this.get_field(column));
					fieldtypes.push(df ? df.fieldtype : "");
				});
				data.shift();
			} else {
				// no column header, map to the existing visible columns
				const visible_columns = grid_rows[0].get_visible_columns();
				let target_column_matched = false;
				visible_columns.forEach((column) => {
					// consider all columns after the target column.
					if (
						target_column_matched ||
						column.fieldname === $(e.target).data("fieldname")
					) {
						fieldnames.push(column.fieldname);
						const df = saashq.meta.get_docfield(doctype, column.fieldname);
						fieldtypes.push(df ? df.fieldtype : "");
						target_column_matched = true;
					}
				});
			}

			let row_idx = locals[doctype][row_docname].idx;
			let data_length = data.length;
			data.forEach((row, i) => {
				setTimeout(() => {
					let blank_row = !row.filter(Boolean).length;
					if (!blank_row) {
						if (row_idx > this.frm.doc[table_field].length) {
							this.grid.add_new_row();
						}

						if (row_idx > 1 && (row_idx - 1) % grid_pagination.page_length === 0) {
							grid_pagination.go_to_page(grid_pagination.page_index + 1);
						}

						const row_name = grid_rows[row_idx - 1].doc.name;
						row.forEach((value, data_index) => {
							if (fieldnames[data_index]) {
								// format value before setting
								value = value_formatter_map[fieldtypes[data_index]]
									? value_formatter_map[fieldtypes[data_index]](value)
									: value;
								saashq.model.set_value(
									doctype,
									row_name,
									fieldnames[data_index],
									value
								);
							}
						});
						row_idx++;
						if (data_length >= 10) {
							let progress = i + 1;
							saashq.show_progress(
								__("Processing"),
								progress,
								data_length,
								null,
								true
							);
						}
					}
				}, 0);
			});
			return false; // Prevent the default handler from running.
		});
	}
	get_field(field_name) {
		let fieldname;
		field_name = field_name.toLowerCase();
		this.grid?.meta?.fields.some((field) => {
			if (saashq.model.no_value_type.includes(field.fieldtype)) {
				return false;
			}

			const is_field_matching = () => {
				return (
					field.fieldname.toLowerCase() === field_name ||
					(field.label || "").toLowerCase() === field_name ||
					(__(field.label, null, field.parent) || "").toLowerCase() === field_name
				);
			};

			if (is_field_matching()) {
				fieldname = field.fieldname;
				return true;
			}
		});
		return fieldname;
	}
	refresh_input() {
		this.grid.refresh();
	}
	get_value() {
		if (this.grid) {
			return this.grid.get_data();
		}
	}
	set_input() {
		//
	}
	validate() {
		return this.get_value();
	}
	check_all_rows() {
		this.$wrapper.find(".grid-row-check")[0].click();
	}
};
