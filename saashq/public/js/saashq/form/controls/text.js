saashq.ui.form.ControlText = class ControlText extends saashq.ui.form.ControlData {
	static html_element = "textarea";
	static horizontal = false;
	make_wrapper() {
		super.make_wrapper();

		const disp_area = this.$wrapper.find(".like-disabled-input");
		disp_area.addClass("for-description");
		disp_area.css("white-space-collapse", "preserve"); // preserve indentation
		if (this.df.max_height) {
			disp_area.css({ "max-height": this.df.max_height, overflow: "auto" });
		}
	}
	make_input() {
		super.make_input();
		this.$input.css({ height: "300px" });
		if (this.df.max_height) {
			this.$input.css({ "max-height": this.df.max_height });
		}
	}
};

saashq.ui.form.ControlLongText = saashq.ui.form.ControlText;
saashq.ui.form.ControlSmallText = class ControlSmallText extends saashq.ui.form.ControlText {
	make_input() {
		super.make_input();
		this.$input.css({ height: "150px" });
	}
};
