import ChartWidget from "../widgets/chart_widget";
import BaseWidget from "../widgets/base_widget";
import ShortcutWidget from "../widgets/shortcut_widget";
import LinksWidget from "../widgets/links_widget";
import OnboardingWidget from "../widgets/onboarding_widget";
import NewWidget from "../widgets/new_widget";
import NumberCardWidget from "../widgets/number_card_widget";
import QuickListWidget from "../widgets/quick_list_widget";
import CustomBlock from "../widgets/custom_block_widget";

saashq.provide("saashq.widget");

saashq.widget.widget_factory = {
	chart: ChartWidget,
	base: BaseWidget,
	shortcut: ShortcutWidget,
	links: LinksWidget,
	onboarding: OnboardingWidget,
	number_card: NumberCardWidget,
	quick_list: QuickListWidget,
	custom_block: CustomBlock,
};

saashq.widget.make_widget = (opts) => {
	const widget_class = saashq.widget.widget_factory[opts.widget_type];
	if (widget_class) {
		return new widget_class(opts);
	} else {
		console.warn("Invalid Widget Name: " + opts.widget_type);
	}
};

export default class WidgetGroup {
	constructor(opts) {
		Object.assign(this, opts);
		this.widgets_list = [];
		this.widgets_dict = {};
		this.widget_order = [];
		this.make();
	}

	make() {
		this.make_container();
		if (this.title) {
			this.set_title();
		} else {
			this.title_area.remove();
		}
		this.widgets && this.make_widgets();
	}

	make_container() {
		const widget_area = $(`<div class="widget-group ${this.class_name || ""}">
				<div class="widget-group-head">
					<div class="widget-group-title"></div>
					<div class="widget-group-control"></div>
				</div>
				<div class="widget-group-body grid-col-${this.columns}">
				</div>
			</div>`);
		this.widget_area = widget_area;
		if (this.hidden) this.widget_area.hide();
		this.title_area = widget_area.find(".widget-group-title");
		this.control_area = widget_area.find(".widget-group-control");
		this.body = widget_area.find(".widget-group-body");
		!this.widgets.length && this.widget_area.hide();
		widget_area.appendTo(this.container);
	}

	set_title() {
		this.title_area[0].innerText = this.title;
	}

	make_widgets() {
		this.body.empty();
		this.widgets.forEach((widget) => {
			this.add_widget(widget);
		});
	}

	add_widget(widget) {
		let widget_object = saashq.widget.make_widget({
			...widget,
			widget_type: this.type,
			container: this.body,
			height: this.height || null,
			options: {
				...this.options,
				on_delete: (name) => this.on_delete(name),
			},
		});

		this.widgets_list.push(widget_object);
		this.widgets_dict[widget.name] = widget_object;

		return widget_object;
	}

	remove_widget(widget_obj) {
		widget_obj.widget.remove();
		this.widgets_list.filter((widget) => {
			if (widget.name == widget_obj.name) return false;
		});
		delete this.widgets_dict[widget_obj.name];
	}

	customize() {
		if (!this.hidden) this.widget_area.show();
		this.widgets_list.forEach((wid) => {
			wid.customize(this.options);
		});

		this.options.allow_create && this.setup_new_widget();
		this.options.allow_sorting && this.setup_sortable();
	}

	setup_new_widget() {
		const max = this.options
			? this.options.max_widget_count || Number.POSITIVE_INFINITY
			: Number.POSITIVE_INFINITY;

		if (this.widgets_list.length < max) {
			this.new_widget = new NewWidget({
				container: this.body,
				type: this.type,
				custom_dialog: this.custom_dialog,
				default_values: this.default_values,
				on_create: (config) => {
					// Remove new widget
					this.new_widget.delete();
					delete this.new_widget;

					config.in_customize_mode = 1;

					// Add new widget and customize it
					let wid = this.add_widget(config);
					wid.customize(this.options);

					// Put back the new widget if required
					if (this.widgets_list.length < max) {
						this.setup_new_widget();
					}
				},
			});
		}
	}

	on_delete(name, setup_new) {
		this.widgets_list = this.widgets_list.filter((wid) => name != wid.name);
		delete this.widgets_dict[name];
		this.update_widget_order();

		if (!this.new_widget && setup_new) this.setup_new_widget();
	}

	update_widget_order() {
		this.widget_order = [];
		this.body.children().each((index, element) => {
			let name = element.dataset.widgetName;
			if (name) {
				this.widget_order.push(name);
			}
		});
	}

	setup_sortable() {
		const container = this.body[0];
		this.sortable = new Sortable(container, {
			animation: 150,
			handle: ".drag-handle",
			onEnd: () => this.update_widget_order(),
		});
	}

	get_widget_config() {
		this.update_widget_order();
		let prepared_dict = {};

		this.widgets_list.forEach((wid) => {
			let config = wid.get_config();
			let name = config.docname ? config.docname : config.name;
			prepared_dict[name] = config;
		});

		return {
			order: this.widget_order,
			widgets: prepared_dict,
		};
	}
}

export class SingleWidgetGroup {
	constructor(opts) {
		Object.assign(this, opts);
		this.widgets_list = [];
		this.widgets_dict = {};
		this.make();
	}

	make() {
		this.add_widget(this.widgets);
	}

	add_widget(widget) {
		let widget_object = saashq.widget.make_widget({
			...widget,
			widget_type: this.type,
			container: this.container,
			height: this.height || null,
			options: {
				...this.options,
				on_delete: () => this.on_delete(),
				on_edit: () => this.on_edit(widget_object),
			},
		});
		this.widgets_list.push(widget_object);
		this.widgets_dict[widget.name] = widget_object;

		return widget_object;
	}

	on_delete() {
		this.api.blocks.delete();
	}

	on_edit(widget_object) {
		this.block.call("on_edit", widget_object);
	}

	customize() {
		this.widgets_list.forEach((wid) => {
			wid.customize(this.options);
		});
	}
}

saashq.widget.WidgetGroup = WidgetGroup;
saashq.widget.SingleWidgetGroup = SingleWidgetGroup;
