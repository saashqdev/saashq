saashq.ui.form.ControlCurrency = class ControlCurrency extends saashq.ui.form.ControlFloat {
	format_for_input(value) {
		var formatted_value = format_number(value, this.get_number_format(), this.get_precision());
		return isNaN(Number(value)) ? "" : formatted_value;
	}

	get_precision() {
		// always round based on field precision or currency's precision
		// this method is also called in this.parse()
		if (typeof this.df.precision != "number" && !this.df.precision) {
			if (saashq.boot.sysdefaults.currency_precision) {
				this.df.precision = saashq.boot.sysdefaults.currency_precision;
			} else {
				this.df.precision = get_number_format_info(this.get_number_format()).precision;
			}
		}

		return this.df.precision;
	}
};
