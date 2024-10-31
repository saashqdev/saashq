saashq.ui.form.on("File", {
	refresh: function (frm) {
		if (!frm.doc.is_folder) {
			// add download button
			frm.add_custom_button(__("Download"), () => frm.trigger("download"), "fa fa-download");
		}

		if (!frm.doc.is_private) {
			frm.dashboard.set_headline(
				__("This file is public. It can be accessed without authentication."),
				"orange"
			);
		}

		frm.toggle_display("preview", false);

		// preview different file types
		frm.trigger("preview_file");

		let is_raster_image = /\.(gif|jpg|jpeg|tiff|png)$/i.test(frm.doc.file_url);
		let is_optimizable = !frm.doc.is_folder && is_raster_image && frm.doc.file_size > 0;

		// add optimize button
		is_optimizable && frm.add_custom_button(__("Optimize"), () => frm.trigger("optimize"));

		// add unzip button
		if (frm.doc.file_name && frm.doc.file_name.split(".").splice(-1)[0] === "zip") {
			frm.add_custom_button(__("Unzip"), () => frm.trigger("unzip"));
		}
		if (frm.doc.file_url) {
			frm.add_web_link(frm.doc.file_url, __("View file"));
		}
	},

	preview_file: function (frm) {
		let $preview = "";
		let file_extension = frm.doc.file_type.toLowerCase();

		if (saashq.utils.is_image_file(frm.doc.file_url)) {
			$preview = $(`<div class="img_preview">
				<img
					class="img-responsive"
					src="${saashq.utils.escape_html(frm.doc.file_url)}"
					onerror="${frm.toggle_display("preview", false)}"
				/>
			</div>`);
		} else if (saashq.utils.is_video_file(frm.doc.file_url)) {
			$preview = $(`<div class="img_preview">
				<video width="480" height="320" controls>
					<source src="${saashq.utils.escape_html(frm.doc.file_url)}">
					${__("Your browser does not support the video element.")}
				</video>
			</div>`);
		} else if (file_extension === "pdf") {
			$preview = $(`<div class="img_preview">
				<object style="background:#323639;" width="100%">
					<embed
						style="background:#323639;"
						width="100%"
						height="1190"
						src="${saashq.utils.escape_html(frm.doc.file_url)}" type="application/pdf"
					>
				</object>
			</div>`);
		} else if (file_extension === "mp3") {
			$preview = $(`<div class="img_preview">
				<audio width="480" height="60" controls>
					<source src="${saashq.utils.escape_html(frm.doc.file_url)}" type="audio/mpeg">
					${__("Your browser does not support the audio element.")}
				</audio >
			</div>`);
		}

		if ($preview) {
			frm.toggle_display("preview", true);
			frm.get_field("preview_html").$wrapper.html($preview);
		}
	},

	download: function (frm) {
		let file_url = frm.doc.file_url;
		if (frm.doc.file_name) {
			file_url = file_url.replace(/#/g, "%23");
		}

		// create temporary link element to simulate a download click
		var link = document.createElement("a");
		link.href = file_url;
		link.download = frm.doc.file_name;
		link.style.display = "none";

		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
	},

	optimize: function (frm) {
		saashq.show_alert(__("Optimizing image..."));
		frm.call("optimize_file").then(() => {
			saashq.show_alert(__("Image optimized"));
		});
	},

	unzip: function (frm) {
		saashq.call({
			method: "saashq.core.api.file.unzip_file",
			args: {
				name: frm.doc.name,
			},
			callback: function () {
				saashq.set_route("List", "File");
			},
		});
	},
});
