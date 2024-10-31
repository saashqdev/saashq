// Copyright (c) 2015, Saashq Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

saashq.ui.form.on("Property Setter", {
	validate: function (frm) {
		if (frm.doc.property_type == "Check" && !["0", "1"].includes(frm.doc.value)) {
			saashq.throw(__("Value for a check field can be either 0 or 1"));
		}
	},
});
