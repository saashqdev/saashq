// Copyright (c) 2019, Saashq Technologies and contributors
// For license information, please see license.txt

saashq.ui.form.on("Notification Log", {
	refresh: function (frm) {
		if (frm.doc.attached_file) {
			frm.trigger("set_attachment");
		} else {
			frm.get_field("attachment_link").$wrapper.empty();
		}
	},

	open_reference_document: function (frm) {
		if (frm.doc?.link) {
			saashq.set_route(frm.doc.link);
			return;
		}
		const dt = frm.doc.document_type;
		const dn = frm.doc.document_name;
		saashq.set_route("Form", dt, dn);
	},

	set_attachment: function (frm) {
		const attachment = JSON.parse(frm.doc.attached_file);

		const $wrapper = frm.get_field("attachment_link").$wrapper;
		$wrapper.html(`
			<div class="attached-file text-medium">
				<div class="ellipsis">
					<i class="fa fa-paperclip"></i>
					<a class="attached-file-link">${attachment.name}.pdf</a>
				</div>
			</div>
		`);

		$wrapper.find(".attached-file-link").click(() => {
			const w = window.open(
				saashq.urllib.get_full_url(`/api/method/saashq.utils.print_format.download_pdf?
					doctype=${encodeURIComponent(attachment.doctype)}
					&name=${encodeURIComponent(attachment.name)}
					&format=${encodeURIComponent(attachment.print_format)}
					&lang=${encodeURIComponent(attachment.lang)}`)
			);
			if (!w) {
				saashq.msgprint(__("Please enable pop-ups"));
			}
		});
	},
});
