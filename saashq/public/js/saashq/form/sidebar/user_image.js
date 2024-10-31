saashq.ui.form.set_user_image = function (frm) {
	var image_section = frm.sidebar.image_section;
	var image_field = frm.meta.image_field;
	var image = frm.doc[image_field];
	var title_image = frm.page.$title_area.find(".title-image");
	var image_actions = frm.sidebar.image_wrapper.find(".sidebar-image-actions");

	image_section.toggleClass("hide", image_field ? false : true);
	title_image.toggleClass("hide", image_field ? false : true);

	if (!image_field) {
		return;
	}

	// if image field has value
	if (image) {
		image = window.cordova && image.indexOf("http") === -1 ? saashq.base_url + image : image;

		image_section.find(".sidebar-image").attr("src", image).removeClass("hide");

		image_section.find(".sidebar-standard-image").addClass("hide");

		title_image.css("background-image", `url("${image}")`).html("");

		image_actions.find(".sidebar-image-change, .sidebar-image-remove").show();
	} else {
		image_section.find(".sidebar-image").attr("src", null).addClass("hide");

		var title = frm.get_title();

		image_section
			.find(".sidebar-standard-image")
			.removeClass("hide")
			.find(".standard-image")
			.html(saashq.get_abbr(title));

		title_image.css("background-image", "").html(saashq.get_abbr(title));

		image_actions.find(".sidebar-image-change").show();
		image_actions.find(".sidebar-image-remove").hide();
	}
};

saashq.ui.form.setup_user_image_event = function (frm) {
	// re-draw image on change of user image
	if (frm.meta.image_field) {
		saashq.ui.form.on(frm.doctype, frm.meta.image_field, function (frm) {
			saashq.ui.form.set_user_image(frm);
		});
	}

	if (frm.meta.image_field && !frm.fields_dict[frm.meta.image_field].df.read_only) {
		frm.sidebar.image_wrapper.on("click", ":not(.sidebar-image-actions)", (e) => {
			let $target = $(e.currentTarget);
			if ($target.is("a.dropdown-toggle, .dropdown")) {
				return;
			}
			let dropdown = frm.sidebar.image_wrapper.find(".sidebar-image-actions .dropdown");
			dropdown.toggleClass("open");
			e.stopPropagation();
		});
	}

	// bind click on image_wrapper
	frm.sidebar.image_wrapper.on(
		"click",
		".sidebar-image-change, .sidebar-image-remove",
		function (e) {
			let $target = $(e.currentTarget);
			var field = frm.get_field(frm.meta.image_field);
			if ($target.is(".sidebar-image-change")) {
				if (!field.$input) {
					field.make_input();
				}
				field.$input.trigger("attach_doc_image");
				// close sidebar
				frm.page.close_sidebar?.();
			} else {
				/// on remove event for a sidebar image wrapper remove attach file.
				frm.attachments.remove_attachment_by_filename(
					frm.doc[frm.meta.image_field],
					function () {
						field.set_value("").then(() => frm.save());
					}
				);
			}
		}
	);
};
