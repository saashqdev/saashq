saashq.provide("saashq.ui");

saashq.ui.Scanner = class Scanner {
	constructor(options) {
		this.dialog = null;
		this.handler = null;
		this.options = options;
		this.is_alive = false;

		if (!("multiple" in this.options)) {
			this.options.multiple = false;
		}
		if (options.container) {
			this.$scan_area = $(options.container);
			this.scan_area_id = saashq.dom.set_unique_id(this.$scan_area);
		}
		if (options.dialog) {
			this.dialog = this.make_dialog();
			this.dialog.show();
		}
	}

	scan() {
		this.load_lib().then(() => this.start_scan());
	}

	start_scan() {
		if (!this.handler) {
			this.handler = new Html5Qrcode(this.scan_area_id); // eslint-disable-line
		}
		this.handler
			.start(
				{ facingMode: "environment" },
				{ fps: 10, qrbox: 250 },
				(decodedText, decodedResult) => {
					if (this.options.on_scan) {
						try {
							this.options.on_scan(decodedResult);
						} catch (error) {
							console.error(error);
						}
					}
					if (!this.options.multiple) {
						this.stop_scan();
						this.hide_dialog();
					}
				},
				(errorMessage) => {
					// parse error, ignore it.
				}
			)
			.catch((err) => {
				this.is_alive = false;
				this.hide_dialog();
				console.error(err);
			});
		this.is_alive = true;
	}

	stop_scan() {
		if (this.handler && this.is_alive) {
			this.handler.stop().then(() => {
				this.is_alive = false;
				this.$scan_area.empty();
				this.hide_dialog();
			});
		}
	}

	make_dialog() {
		let dialog = new saashq.ui.Dialog({
			title: __("Scan QRCode"),
			fields: [
				{
					fieldtype: "HTML",
					fieldname: "scan_area",
				},
			],
			on_page_show: () => {
				this.$scan_area = dialog.get_field("scan_area").$wrapper;
				this.$scan_area.addClass("barcode-scanner");
				this.scan_area_id = saashq.dom.set_unique_id(this.$scan_area);
				this.scan();
			},
			on_hide: () => {
				this.stop_scan();
			},
		});
		return dialog;
	}

	hide_dialog() {
		this.dialog && this.dialog.hide();
	}

	load_lib() {
		return saashq.require("/assets/saashq/node_modules/html5-qrcode/html5-qrcode.min.js");
	}
};
