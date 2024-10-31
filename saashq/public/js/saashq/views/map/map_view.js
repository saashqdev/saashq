/**
 * saashq.views.MapView
 */
saashq.provide("saashq.utils");
saashq.provide("saashq.views");

saashq.views.MapView = class MapView extends saashq.views.ListView {
	get view_name() {
		return "Map";
	}

	setup_defaults() {
		super.setup_defaults();
		this.page_title = __("{0} Map", [this.page_title]);
	}

	setup_view() {}

	on_filter_change() {
		this.get_coords();
	}

	render() {
		this.get_coords().then(() => {
			this.render_map_view();
		});
		this.$paging_area.find(".level-left").append("<div></div>");
	}

	render_map_view() {
		this.map_id = saashq.dom.get_unique_id();

		this.$result.html(`<div id="${this.map_id}" class="map-view-container"></div>`);

		L.Icon.Default.imagePath = saashq.utils.map_defaults.image_path;
		this.map = L.map(this.map_id).setView(
			saashq.utils.map_defaults.center,
			saashq.utils.map_defaults.zoom
		);

		L.tileLayer(saashq.utils.map_defaults.tiles, saashq.utils.map_defaults.options).addTo(
			this.map
		);

		L.control.scale().addTo(this.map);
		if (this.coords.features && this.coords.features.length) {
			this.coords.features.forEach((coords) =>
				L.geoJSON(coords).bindPopup(coords.properties.name).addTo(this.map)
			);
			let lastCoords = this.coords.features[0].geometry.coordinates.reverse();
			this.map.panTo(lastCoords, 8);
		}
	}

	get_coords() {
		let get_coords_method =
			(this.settings && this.settings.get_coords_method) || "saashq.geo.utils.get_coords";

		if (
			cur_list.meta.fields.find(
				(i) => i.fieldname === "location" && i.fieldtype === "Geolocation"
			)
		) {
			this.type = "location_field";
		} else if (
			cur_list.meta.fields.find((i) => i.fieldname === "latitude") &&
			cur_list.meta.fields.find((i) => i.fieldname === "longitude")
		) {
			this.type = "coordinates";
		}
		return saashq
			.call({
				method: get_coords_method,
				args: {
					doctype: this.doctype,
					filters: cur_list.filter_area.get(),
					type: this.type,
				},
			})
			.then((r) => {
				this.coords = r.message;
			});
	}

	get required_libs() {
		return [
			"assets/saashq/js/lib/leaflet/leaflet.css",
			"assets/saashq/js/lib/leaflet/leaflet.js",
		];
	}
};
