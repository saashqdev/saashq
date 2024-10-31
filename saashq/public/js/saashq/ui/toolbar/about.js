saashq.provide("saashq.ui.misc");
saashq.ui.misc.about = function () {
	if (!saashq.ui.misc.about_dialog) {
		var d = new saashq.ui.Dialog({ title: __("Saashq Framework") });

		$(d.body).html(
			repl(
				`<div>
					<p>${__("Open Source Applications for the Web")}</p>
					<p><i class='fa fa-globe fa-fw'></i>
						${__("Website")}:
						<a href='https://saashqframework.com' target='_blank'>https://saashqframework.com</a></p>
					<p><i class='fa fa-github fa-fw'></i>
						${__("Source")}:
						<a href='https://github.com/saashq' target='_blank'>https://github.com/saashq</a></p>
					<p><i class='fa fa-graduation-cap fa-fw'></i>
						Saashq School: <a href='https://saashq.school' target='_blank'>https://saashq.school</a></p>
					<p><i class='fa fa-linkedin fa-fw'></i>
						Linkedin: <a href='https://linkedin.com/company/saashq-tech' target='_blank'>https://linkedin.com/company/saashq-tech</a></p>
					<p><i class='fa fa-twitter fa-fw'></i>
						Twitter: <a href='https://twitter.com/saashqtech' target='_blank'>https://twitter.com/saashqtech</a></p>
					<p><i class='fa fa-youtube fa-fw'></i>
						YouTube: <a href='https://www.youtube.com/@saashqtech' target='_blank'>https://www.youtube.com/@saashqtech</a></p>
					<hr>
					<h4>${__("Installed Apps")}</h4>
					<div id='about-app-versions'>${__("Loading versions...")}</div>
					<p>
						<b>
							<a href="/attribution" target="_blank" class="text-muted">
								${__("Dependencies & Licenses")}
							</a>
						</b>
					</p>
					<hr>
					<p class='text-muted'>${__("&copy; Saashq Technologies Pvt. Ltd. and contributors")} </p>
					</div>`,
				saashq.app
			)
		);

		saashq.ui.misc.about_dialog = d;

		saashq.ui.misc.about_dialog.on_page_show = function () {
			if (!saashq.versions) {
				saashq.call({
					method: "saashq.utils.change_log.get_versions",
					callback: function (r) {
						show_versions(r.message);
					},
				});
			} else {
				show_versions(saashq.versions);
			}
		};

		var show_versions = function (versions) {
			var $wrap = $("#about-app-versions").empty();
			$.each(Object.keys(versions).sort(), function (i, key) {
				var v = versions[key];
				let text;
				if (v.branch) {
					text = $.format("<p><b>{0}:</b> v{1} ({2})<br></p>", [
						v.title,
						v.branch_version || v.version,
						v.branch,
					]);
				} else {
					text = $.format("<p><b>{0}:</b> v{1}<br></p>", [v.title, v.version]);
				}
				$(text).appendTo($wrap);
			});

			saashq.versions = versions;
		};
	}

	saashq.ui.misc.about_dialog.show();
};
