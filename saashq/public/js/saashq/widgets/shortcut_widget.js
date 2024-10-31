import Widget from "./base_widget.js";

saashq.provide("saashq.utils");

export default class ShortcutWidget extends Widget {
	constructor(opts) {
		opts.shadow = true;
		super(opts);
	}

	get_config() {
		return {
			name: this.name,
			icon: this.icon,
			label: this.label,
			format: this.format,
			link_to: this.link_to,
			doc_view: this.doc_view,
			color: this.color,
			restrict_to_domain: this.restrict_to_domain,
			stats_filter: this.stats_filter,
			type: this.type,
			url: this.url,
			kanban_board: this.kanban_board,
		};
	}

	setup_events() {
		this.widget.click((e) => {
			if (this.in_customize_mode) return;

			let route = saashq.utils.generate_route({
				route: this.route,
				name: this.link_to,
				type: this.type,
				is_query_report: this.is_query_report,
				doctype: this.ref_doctype,
				doc_view: this.doc_view,
				kanban_board: this.kanban_board,
			});

			let filters = saashq.utils.get_filter_from_json(this.stats_filter);
			if (this.type == "DocType" && filters) {
				saashq.route_options = filters;
			}

			if (e.ctrlKey || e.metaKey) {
				saashq.open_in_new_tab = true;
			}

			if (this.type == "URL") {
				window.open(this.url, "_blank");
				return;
			}

			saashq.set_route(route);
		});
	}

	set_actions() {
		if (this.in_customize_mode) return;

		$(saashq.utils.icon("es-line-arrow-up-right", "xs", "", "", "ml-2")).appendTo(
			this.action_area
		);

		this.widget.addClass("shortcut-widget-box");

		// Make it tabbable
		this.widget.attr({
			role: "link",
			tabindex: 0,
			"aria-label": this.label,
		});

		let filters = saashq.utils.process_filter_expression(this.stats_filter);

		if (
			this.type == "DocType" &&
			this.doc_view != "New" &&
			!saashq.boot.single_types.includes(this.link_to)
		) {
			saashq.db
				.count(this.link_to, {
					filters: filters || [],
				})
				.then((count) => this.set_count(count));
		}
	}

	set_count(count) {
		const get_label = () => {
			if (this.format) {
				return __(this.format).replace(/{}/g, count);
			}
			return count;
		};

		this.action_area.empty();
		const label = get_label();
		let color = this.color && count ? this.color.toLowerCase() : "gray";
		$(
			`<div class="indicator-pill no-indicator-dot ellipsis ${color}">${label}</div>`
		).appendTo(this.action_area);

		$(saashq.utils.icon("es-line-arrow-up-right", "xs", "", "", "ml-2")).appendTo(
			this.action_area
		);
	}
}
