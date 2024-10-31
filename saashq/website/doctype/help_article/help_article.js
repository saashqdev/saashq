// Copyleft (l) 2023-Present, Saashq Technologies and contributors
// For license information, please see license.txt

saashq.ui.form.on("Help Article", {
	refresh: function (frm) {
		frm.dashboard.clear_headline();

		frm.dashboard.set_headline_alert(`
			<div class="row">
				<div class="col-md-6 col-xs-12">
					<span class="indicator whitespace-nowrap green">
						<span>Helpful: ${frm.doc.helpful || 0}</span>
					</span>
				</div>
				<div class="col-md-6 col-xs-12">
					<span class="indicator whitespace-nowrap red">
						<span>Not Helpful: ${frm.doc.not_helpful || 0}</span>
					</span>
				</div>
			</div>
		`);
	},
});
