saashq.ui.form.ControlDate = class ControlDate extends saashq.ui.form.ControlData {
	static trigger_change_on_input_event = false;
	make_input() {
		super.make_input();
		this.make_picker();
	}
	make_picker() {
		this.set_date_options();
		this.set_datepicker();
		this.set_t_for_today();
	}
	set_formatted_input(value) {
		if (value === "Today") {
			value = this.get_now_date();
		}

		super.set_formatted_input(value);
		if (this.timepicker_only) return;
		if (!this.datepicker) return;
		if (!value) {
			this.datepicker.clear();
			return;
		}

		let should_refresh = this.last_value && this.last_value !== value;

		if (!should_refresh) {
			if (this.datepicker.selectedDates.length > 0) {
				// if date is selected but different from value, refresh
				const selected_date = moment(this.datepicker.selectedDates[0]).format(
					this.date_format
				);

				should_refresh = selected_date !== value;
			} else {
				// if datepicker has no selected date, refresh
				should_refresh = true;
			}
		}

		if (should_refresh) {
			this.datepicker.selectDate(saashq.datetime.str_to_obj(value));
		}
	}
	set_date_options() {
		// webformTODO:
		let sysdefaults = saashq.boot.sysdefaults;

		let lang = "en";
		saashq.boot.user && (lang = saashq.boot.user.language);
		if (!$.fn.datepicker.language[lang]) {
			lang = "en";
		}

		let date_format =
			sysdefaults && sysdefaults.date_format ? sysdefaults.date_format : "yyyy-mm-dd";

		this.today_text = __("Today");
		this.date_format = saashq.defaultDateFormat;
		this.datepicker_options = {
			language: lang,
			autoClose: true,
			todayButton: true,
			dateFormat: date_format,
			startDate: this.get_start_date(),
			keyboardNav: false,
			minDate: this.df.min_date,
			maxDate: this.df.max_date,
			firstDay: saashq.datetime.get_first_day_of_the_week_index(),
			onSelect: () => {
				this.$input.trigger("change");
			},
			onShow: () => {
				this.datepicker.$datepicker
					.find(".datepicker--button:visible")
					.text(this.today_text);

				this.update_datepicker_position();
			},
			...this.get_df_options(),
		};
	}

	get_start_date() {
		return this.get_now_date();
	}

	set_datepicker() {
		this.$input.datepicker(this.datepicker_options);
		this.datepicker = this.$input.data("datepicker");

		// today button didn't work as expected,
		// so explicitly bind the event
		this.datepicker.$datepicker.find('[data-action="today"]').click(() => {
			this.datepicker.selectDate(this.get_now_date());
			this.datepicker.hide();
		});
	}
	update_datepicker_position() {
		if (!this.frm) return;
		// show datepicker above or below the input
		// based on scroll position
		// We have to bodge around the timepicker getting its position
		// wrong by 42px when opening upwards.
		const $header = $(".page-head");
		const header_bottom = $header.position().top + $header.outerHeight();
		const picker_height = this.datepicker.$datepicker.outerHeight() + 12;
		const picker_top = this.$input.offset().top - $(window).scrollTop() - picker_height;

		var position = "top left";
		// 12 is the default datepicker.opts[offset]
		if (picker_top <= header_bottom) {
			position = "bottom left";
			if (this.timepicker_only) this.datepicker.opts["offset"] = 12;
		} else {
			// To account for 42px incorrect positioning
			if (this.timepicker_only) this.datepicker.opts["offset"] = -30;
		}

		this.datepicker.update("position", position);
	}
	get_now_date() {
		return saashq.datetime
			.convert_to_system_tz(saashq.datetime.now_date(true), false)
			.toDate();
	}
	set_t_for_today() {
		var me = this;
		this.$input.on("keydown", function (e) {
			if (e.which === 84) {
				// 84 === t
				if (me.df.fieldtype == "Date") {
					me.set_value(saashq.datetime.nowdate());
				}
				if (me.df.fieldtype == "Datetime") {
					me.set_value(saashq.datetime.now_datetime());
				}
				if (me.df.fieldtype == "Time") {
					me.set_value(saashq.datetime.now_time());
				}
				return false;
			}
		});
	}

	eval_expression(value, type) {
		if (!value || !type) {
			return value;
		}
		const parsed_components = value.match(/[\+\-]\s*\d*\.?\d+\s*[a-zA-Z]/g);

		let system_fmt;
		switch (type) {
			case "date":
				system_fmt = "YYYY-MM-DD";
				value = saashq.datetime.user_to_str(value, false);
				break;

			case "time":
				system_fmt = "HH:mm:ss";
				value = saashq.datetime.user_to_str(value, true);
				break;

			case "datetime":
				system_fmt = "YYYY-MM-DD HH:mm:ss";
				value = saashq.datetime.user_to_str(value, false);
				break;
		}

		if (!parsed_components) {
			return value;
		}

		let time_to_add = {};
		parsed_components.forEach((component) => {
			let operator = component.match(/[\+\-]/)[0];
			let number = flt(component.match(/\d*\.?\d+/)[0]);
			let unit = component.match(/[a-zA-Z]+/)[0];
			let period;

			if (operator === "-") {
				number = -number;
			}

			if (["datetime", "date"].includes(type)) {
				if (unit.toLowerCase() === "d") {
					period = "days";
				} else if (unit === "M") {
					period = "months";
				} else if (unit.toLowerCase() === "y") {
					period = "years";
				}
			}

			if (["datetime", "time"].includes(type)) {
				if (unit.toLowerCase() === "h") {
					period = "hours";
				} else if (unit === "m") {
					period = "minutes";
				} else if (unit.toLowerCase() === "s") {
					period = "seconds";
				}
			}

			if (period) {
				time_to_add[period] = (time_to_add[period] || 0) + number;
			}
		});

		if (Object.keys(time_to_add).length) {
			value = moment(value, system_fmt).add(time_to_add).format(system_fmt);
		}

		return value;
	}

	parse(value) {
		if (value) {
			if (value == "Invalid date") {
				return "";
			}
			return this.eval_expression(value, "date");
		}
	}
	format_for_input(value) {
		if (value) {
			return saashq.datetime.str_to_user(value, false, true);
		}
		return "";
	}
	validate(value) {
		if (value && !saashq.datetime.validate(value)) {
			let sysdefaults = saashq.sys_defaults;
			let date_format =
				sysdefaults && sysdefaults.date_format ? sysdefaults.date_format : "yyyy-mm-dd";
			saashq.msgprint(__("Date {0} must be in format: {1}", [value, date_format]));
			return "";
		}
		return value;
	}
	get_df_options() {
		let df_options = this.df.options;
		if (!df_options) return {};

		let options = {};
		if (typeof df_options === "string") {
			try {
				options = JSON.parse(df_options);
			} catch (error) {
				console.warn(`Invalid JSON in options of "${this.df.fieldname}"`);
			}
		} else if (typeof df_options === "object") {
			options = df_options;
		}
		return options;
	}
};
