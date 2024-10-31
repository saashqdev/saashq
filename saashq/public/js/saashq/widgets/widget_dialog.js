class WidgetDialog {
	constructor(opts) {
		Object.assign(this, opts);
		this.editing = Boolean(this.values && Object.keys(this.values).length);
	}

	make() {
		this.make_dialog();
		this.setup_dialog_events();
		this.dialog.show();

		window.cur_dialog = this.dialog;
		this.editing && this.set_default_values();
	}

	make_dialog() {
		this.dialog = new saashq.ui.Dialog({
			title: this.get_title(),
			fields: this.get_fields(),
			primary_action: (data) => {
				data = this.process_data(data);

				if (!this.editing && !data.name) {
					data.name = `${this.type}-${this.label}-${saashq.utils.get_random(20)}`;
				}

				this.dialog.hide();
				this.primary_action(data);
			},
			primary_action_label: this.primary_action_label || __("Add"),
		});
	}

	get_title() {
		if (this.editing) {
			switch (this.type) {
				case "chart":
					return __("Edit Chart");
				case "shortcut":
					return __("Edit Shortcut");
				case "links":
					return __("Edit Links");
				case "number_card":
					return __("Edit Number Card");
				case "onboarding":
					return __("Edit Onboarding");
				case "quick_list":
					return __("Edit Quick List");
				case "custom_block":
					return __("Edit Custom Block");
				default:
					return __("Edit {0}", [__(saashq.model.unscrub(this.type))]);
			}
		}

		switch (this.type) {
			case "chart":
				return __("New Chart");
			case "shortcut":
				return __("New Shortcut");
			case "links":
				return __("New Links");
			case "number_card":
				return __("New Number Card");
			case "onboarding":
				return __("New Onboarding");
			case "quick_list":
				return __("New Quick List");
			case "custom_block":
				return __("New Custom Block");
			default:
				return __("New {0}", [__(saashq.model.unscrub(this.type))]);
		}
	}

	get_fields() {
		//
	}

	set_default_values() {
		return this.dialog.set_values(this.values);
	}

	process_data(data) {
		return data;
	}

	setup_dialog_events() {
		//
	}

	hide_field(fieldname) {
		this.dialog.set_df_property(fieldname, "hidden", true);
	}

	show_field(fieldname) {
		this.dialog.set_df_property(fieldname, "hidden", false);
	}

	setup_filter(doctype) {
		if (this.filter_group) {
			this.filter_group.wrapper.empty();
			delete this.filter_group;
		}

		let $loading = this.dialog.get_field("filter_area_loading").$wrapper;
		$(`<span class="text-muted">${__("Loading Filters...")}</span>`).appendTo($loading);

		this.filters = [];

		this.generate_filter_from_json && this.generate_filter_from_json();

		this.filter_group = new saashq.ui.FilterGroup({
			parent: this.dialog.get_field("filter_area").$wrapper,
			doctype: doctype,
			on_change: () => {},
		});

		saashq.model.with_doctype(doctype, () => {
			this.filter_group.add_filters_to_filter_group(this.filters);
			this.hide_field("filter_area_loading");
			this.show_field("filter_area");
		});
	}
}

class ChartDialog extends WidgetDialog {
	constructor(opts) {
		super(opts);
	}

	get_fields() {
		return [
			{
				fieldtype: "Link",
				fieldname: "chart_name",
				label: __("Chart Name"),
				options: "Dashboard Chart",
				reqd: 1,
			},
			{
				fieldtype: "Data",
				fieldname: "label",
				label: "Label",
			},
		];
	}

	process_data(data) {
		data.label = data.label ? data.label : data.chart_name;
		return data;
	}
}
class QuickListDialog extends WidgetDialog {
	constructor(opts) {
		super(opts);
	}

	get_fields() {
		return [
			{
				fieldtype: "Link",
				fieldname: "document_type",
				label: __("DocType"),
				options: "DocType",
				reqd: 1,
				onchange: () => {
					this.document_type = this.dialog.get_value("document_type");
					this.document_type && this.setup_filter(this.document_type);
				},
				get_query: () => {
					return {
						filters: {
							issingle: 0,
							istable: 0,
						},
					};
				},
			},
			{
				fieldtype: "Data",
				fieldname: "label",
				label: __("Label"),
			},
			{
				fieldtype: "Section Break",
				fieldname: "filter_section",
				label: __("Add Filters"),
				depends_on: "eval: doc.document_type",
			},
			{
				fieldtype: "HTML",
				fieldname: "filter_area_loading",
			},
			{
				fieldtype: "HTML",
				fieldname: "filter_area",
			},
		];
	}

	generate_filter_from_json() {
		if (this.values && this.values.quick_list_filter) {
			this.filters = saashq.utils.get_filter_from_json(
				this.values.quick_list_filter,
				this.values.document_type
			);
		}
	}

	process_data(data) {
		if (this.filter_group) {
			let filters = this.filter_group.get_filters();
			data.quick_list_filter = JSON.stringify(filters);
		}

		data.label = data.label ? data.label : data.document_type;
		return data;
	}
}

class OnboardingDialog extends WidgetDialog {
	constructor(opts) {
		super(opts);
	}

	get_fields() {
		return [
			{
				fieldtype: "Link",
				fieldname: "onboarding_name",
				label: __("Onboarding Name"),
				options: "Module Onboarding",
				reqd: 1,
			},
		];
	}
}

class CardDialog extends WidgetDialog {
	constructor(opts) {
		super(opts);
	}

	get_fields() {
		let me = this;
		return [
			{
				fieldtype: "Data",
				fieldname: "label",
				label: __("Label"),
			},
			{
				fieldtype: "HTML Editor",
				fieldname: "description",
				label: __("Description"),
				max_height: "7rem",
			},
			{
				fieldname: "links",
				fieldtype: "Table",
				label: __("Card Links"),
				editable_grid: 1,
				data: me.values ? JSON.parse(me.values.links) : [],
				get_data: () => {
					return me.values ? JSON.parse(me.values.links) : [];
				},
				fields: [
					{
						fieldname: "link_type",
						fieldtype: "Select",
						in_list_view: 1,
						label: __("Link Type"),
						reqd: 1,
						options: ["DocType", "Page", "Report"],
					},
					{
						fieldname: "link_to",
						fieldtype: "Dynamic Link",
						in_list_view: 1,
						label: __("Link To"),
						reqd: 1,
						get_options: (df) => {
							return df.doc.link_type;
						},
						get_query: function (df) {
							if (df.link_type == "DocType") {
								return {
									filters: {
										istable: 0,
									},
								};
							}
						},
					},
					{
						fieldname: "label",
						fieldtype: "Data",
						in_list_view: 1,
						label: __("Label"),
					},
					{
						fieldname: "icon",
						fieldtype: "Icon",
						label: "Icon",
					},
					{
						fieldname: "dependencies",
						fieldtype: "Data",
						label: __("Dependencies"),
					},
					{
						fieldname: "only_for",
						fieldtype: "Link",
						label: __("Only for"),
						options: "Country",
					},
					{
						default: "0",
						fieldname: "onboard",
						fieldtype: "Check",
						label: __("Onboard"),
					},
					{
						default: "0",
						fieldname: "is_query_report",
						fieldtype: "Check",
						label: __("Is Query Report"),
					},
				],
			},
		];
	}

	process_data(data) {
		let message = "";

		if (!data.links) {
			message = __("You must add atleast one link.");
		} else {
			data.links.map((item, idx) => {
				let row = idx + 1;

				if (!item.link_type) {
					message = __("Following fields have missing values") + ": <br><br><ul>";
					message += `<li>${__("Link Type in Row")} ${row}</li>`;
				}

				if (!item.link_to) {
					message += `<li>${__("Link To in Row")} ${row}</li>`;
				}

				item.label = item.label ? item.label : item.link_to;
			});
		}

		if (message) {
			message += "</ul>";
			saashq.throw({
				message: __(message),
				title: __("Missing Values Required"),
				indicator: "orange",
			});
		}

		data.label = data.label ? data.label : data.chart_name;
		return data;
	}
}

class ShortcutDialog extends WidgetDialog {
	constructor(opts) {
		super(opts);
	}

	hide_filters() {
		this.hide_field("count_section_break");
		this.hide_field("filters_section_break");
	}

	show_filters() {
		this.show_field("count_section_break");
		this.show_field("filters_section_break");
	}

	get_fields() {
		return [
			{
				fieldtype: "Select",
				fieldname: "type",
				label: __("Type"),
				reqd: 1,
				options: "DocType\nReport\nPage\nDashboard\nURL",
				initial_value: "DocType",
				onchange: () => {
					if (this.dialog.get_value("type") == "DocType") {
						this.dialog.fields_dict.link_to.get_query = () => {
							return {
								query: "saashq.core.report.permitted_documents_for_user.permitted_documents_for_user.query_doctypes",
								filters: {
									user: saashq.session.user,
									include_single_doctypes: true,
								},
							};
						};
					} else {
						this.dialog.fields_dict.link_to.get_query = null;
					}
				},
			},
			{
				fieldtype: "Dynamic Link",
				fieldname: "link_to",
				label: __("Link To"),
				options: "type",
				onchange: () => {
					const doctype = this.dialog.get_value("link_to");
					if (doctype && this.dialog.get_value("type") == "DocType") {
						saashq.model.with_doctype(doctype, async () => {
							let meta = saashq.get_meta(doctype);

							if (doctype && saashq.boot.single_types.includes(doctype)) {
								this.hide_filters();
							} else if (doctype) {
								this.setup_filter(doctype);
								this.show_filters();
							}

							const views = ["List", "Report Builder", "Dashboard", "New"];
							if (meta.is_tree === 1) views.push("Tree");
							if (meta.image_field) views.push("Image");
							if (saashq.boot.calendars.includes(doctype)) views.push("Calendar");

							const response = await saashq.db.get_value(
								"Kanban Board",
								{ reference_doctype: doctype },
								"name"
							);
							if (response?.message?.name) views.push("Kanban");

							this.dialog.set_df_property("doc_view", "options", views.join("\n"));
						});
					} else {
						this.hide_filters();
					}
				},
				depends_on: (s) => s.type != "URL",
				mandatory_depends_on: (s) => s.type != "URL",
			},
			{
				fieldtype: "Data",
				fieldname: "label",
				label: __("Label"),
			},
			{
				fieldtype: "Data",
				fieldname: "url",
				label: __("URL"),
				default: "",
				depends_on: (s) => s.type == "URL",
				mandatory_depends_on: (s) => s.type == "URL",
			},
			{
				fieldtype: "Select",
				fieldname: "doc_view",
				label: __("DocType View"),
				options: "List\nReport Builder\nDashboard\nTree\nNew\nCalendar\nKanban\nImage",
				description: __(
					"Which view of the associated DocType should this shortcut take you to?"
				),
				default: "List",
				depends_on: (state) => {
					if (this.dialog) {
						let doctype = this.dialog.get_value("link_to");
						let is_single = saashq.boot.single_types.includes(doctype);
						return doctype && state.type == "DocType" && !is_single;
					}

					return false;
				},
				onchange: () => {
					if (this.dialog.get_value("doc_view") == "Kanban") {
						this.dialog.fields_dict.kanban_board.get_query = () => {
							return {
								filters: {
									reference_doctype: this.dialog.get_value("link_to"),
								},
							};
						};
					} else {
						this.dialog.fields_dict.link_to.get_query = null;
					}
				},
			},
			{
				fieldtype: "Link",
				fieldname: "kanban_board",
				label: __("Kanban Board"),
				options: "Kanban Board",
				depends_on: () => {
					let doc_view = this.dialog?.get_value("doc_view");
					return doc_view == "Kanban";
				},
				mandatory_depends_on: () => {
					let doc_view = this.dialog?.get_value("doc_view");
					return doc_view == "Kanban";
				},
			},
			{
				fieldtype: "Section Break",
				fieldname: "filters_section_break",
				label: __("Count Filter"),
				hidden: 1,
			},
			{
				fieldtype: "HTML",
				fieldname: "filter_area_loading",
			},
			{
				fieldtype: "HTML",
				fieldname: "filter_area",
				hidden: 1,
			},
			{
				fieldtype: "Section Break",
				fieldname: "count_section_break",
				label: __("Count Customizations"),
				hidden: 1,
			},
			{
				fieldtype: "Select",
				fieldname: "color",
				label: __("Color"),
				options: ["Grey", "Green", "Red", "Orange", "Pink", "Yellow", "Blue", "Cyan"],
				default: "Grey",
				input_class: "color-select",
				onchange: () => {
					let color = this.dialog.fields_dict.color.value.toLowerCase();
					let $select = this.dialog.fields_dict.color.$input;
					if (!$select.parent().find(".color-box").get(0)) {
						$(`<div class="color-box"></div>`).insertBefore($select.get(0));
					}
					$select
						.parent()
						.find(".color-box")
						.get(0).style.backgroundColor = `var(--text-on-${color})`;
				},
			},
			{
				fieldtype: "Data",
				fieldname: "format",
				label: __("Format"),
				description: __("For Example: {} Open"),
			},
		];
	}

	set_default_values() {
		super.set_default_values().then(() => {
			this.dialog.fields_dict.link_to.df.onchange();
		});
	}

	generate_filter_from_json() {
		if (this.values && this.values.stats_filter) {
			this.filters = saashq.utils.get_filter_from_json(
				this.values.stats_filter,
				this.values.link_to
			);
		}
	}

	process_data(data) {
		if (this.dialog.get_value("type") == "DocType" && this.filter_group) {
			let filters = this.filter_group.get_filters();
			data.stats_filter = JSON.stringify(filters);
		}

		data.label = data.label ? data.label : saashq.model.unscrub(data.link_to);

		if (data.url) {
			let _url = data.url;
			if (data.url.startsWith("/")) {
				_url = saashq.urllib.get_base_url() + data.url;
			}
			!validate_url(_url) &&
				saashq.throw({
					message: __("<b>{0}</b> is not a valid URL", [data.url]),
					title: __("Invalid URL"),
					indicator: "red",
				});

			if (!data.label) {
				data.label = "No Label (URL)";
			}
		}

		return data;
	}
}

class NumberCardDialog extends WidgetDialog {
	constructor(opts) {
		super(opts);
	}

	get_fields() {
		let fields;

		if (this.for_workspace) {
			return [
				{
					fieldtype: "Link",
					fieldname: "number_card_name",
					label: __("Number Card"),
					options: "Number Card",
					reqd: 1,
					get_query: () => {
						return {
							query: "saashq.desk.doctype.number_card.number_card.get_cards_for_user",
							filters: {
								document_type: this.document_type,
							},
						};
					},
				},
				{
					fieldtype: "Data",
					fieldname: "label",
					label: __("Label"),
				},
			];
		}

		fields = [
			{
				fieldtype: "Select",
				label: __("Choose Existing Card or create New Card"),
				fieldname: "new_or_existing",
				options: ["New Card", "Existing Card"],
			},
			{
				fieldtype: "Link",
				fieldname: "card",
				label: __("Number Cards"),
				options: "Number Card",
				get_query: () => {
					return {
						query: "saashq.desk.doctype.number_card.number_card.get_cards_for_user",
						filters: {
							document_type: this.document_type,
						},
					};
				},
				depends_on: 'eval: doc.new_or_existing == "Existing Card"',
			},
			{
				fieldtype: "Section Break",
				fieldname: "sb_1",
				depends_on: 'eval: doc.new_or_existing == "New Card"',
			},
			{
				label: __("Label"),
				fieldname: "label",
				fieldtype: "Data",
				mandatory_depends_on: 'eval: doc.new_or_existing == "New Card"',
			},
			{
				label: __("Doctype"),
				fieldname: "document_type",
				fieldtype: "Link",
				options: "DocType",
				onchange: () => {
					this.document_type = this.dialog.get_value("document_type");
					this.set_aggregate_function_fields(this.dialog.get_values());
					this.setup_filter(this.document_type);
				},
				hidden: 1,
			},
			{
				label: __("Color"),
				fieldname: "color",
				fieldtype: "Color",
			},
			{
				label: __("Function"),
				fieldname: "function",
				fieldtype: "Select",
				options: ["Count", "Sum", "Average", "Minimum", "Maximum"],
				mandatory_depends_on: 'eval: doc.new_or_existing == "New Card"',
			},
			{
				label: __("Function Based On"),
				fieldname: "aggregate_function_based_on",
				fieldtype: "Select",
				depends_on: "eval: doc.function !== 'Count'",
				mandatory_depends_on:
					'eval: doc.function !== "Count" && doc.new_or_existing == "New Card"',
			},
			{
				fieldtype: "Section Break",
				fieldname: "sb_1",
				label: __("Add Filters"),
				depends_on: 'eval: doc.new_or_existing == "New Card"',
			},
			{
				fieldtype: "HTML",
				fieldname: "filter_area_loading",
			},
			{
				fieldtype: "HTML",
				fieldname: "filter_area",
				hidden: 1,
			},
			{
				fieldtype: "Section Break",
				fieldname: "sb_1",
			},
		];

		return fields;
	}

	setup_dialog_events() {
		if (!this.document_type && !this.for_workspace) {
			if (this.default_values && this.default_values["doctype"]) {
				this.document_type = this.default_values["doctype"];
				this.setup_filter(this.default_values["doctype"]);
				this.set_aggregate_function_fields();
			} else {
				this.show_field("document_type");
			}
		}
	}

	set_aggregate_function_fields() {
		let aggregate_function_fields = [];
		if (this.document_type && saashq.get_meta(this.document_type)) {
			saashq.get_meta(this.document_type).fields.map((df) => {
				if (saashq.model.numeric_fieldtypes.includes(df.fieldtype)) {
					if (df.fieldtype == "Currency") {
						if (!df.options || df.options !== "Company:company:default_currency") {
							return;
						}
					}
					aggregate_function_fields.push({ label: df.label, value: df.fieldname });
				}
			});
		}
		this.dialog.set_df_property(
			"aggregate_function_based_on",
			"options",
			aggregate_function_fields
		);
	}

	process_data(data) {
		if (this.for_workspace) {
			data.label = data.label ? data.label : data.number_card_name;
			return data;
		}

		if (data.new_or_existing == "Existing Card") {
			data.name = data.card;
		}
		data.stats_filter = this.filter_group && JSON.stringify(this.filter_group.get_filters());
		data.document_type = this.document_type;
		return data;
	}
}

class CustomBlockDialog extends WidgetDialog {
	constructor(opts) {
		super(opts);
	}

	get_fields() {
		return [
			{
				fieldtype: "Link",
				fieldname: "custom_block_name",
				label: "Custom Block Name",
				options: "Custom HTML Block",
				reqd: 1,
				get_query: () => {
					return {
						query: "saashq.desk.doctype.custom_html_block.custom_html_block.get_custom_blocks_for_user",
					};
				},
			},
		];
	}
}

export default function get_dialog_constructor(type) {
	const widget_map = {
		chart: ChartDialog,
		shortcut: ShortcutDialog,
		links: CardDialog,
		onboarding: OnboardingDialog,
		quick_list: QuickListDialog,
		number_card: NumberCardDialog,
		custom_block: CustomBlockDialog,
	};

	return widget_map[type] || WidgetDialog;
}
