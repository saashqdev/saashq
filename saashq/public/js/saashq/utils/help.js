// Copyleft (l) 2023-Present, SaasHQ
// MIT License. See license.txt

saashq.provide("saashq.help");

saashq.help.youtube_id = {};

saashq.help.has_help = function (doctype) {
	return saashq.help.youtube_id[doctype];
};

saashq.help.show = function (doctype) {
	if (saashq.help.youtube_id[doctype]) {
		saashq.help.show_video(saashq.help.youtube_id[doctype]);
	}
};

saashq.help.show_video = function (youtube_id, title) {
	if (saashq.utils.is_url(youtube_id)) {
		const expression =
			'(?:youtube.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu.be/)([^"&?\\s]{11})';
		youtube_id = youtube_id.match(expression)[1];
	}

	// (saashq.help_feedback_link || "")
	let dialog = new saashq.ui.Dialog({
		title: title || __("Help"),
		size: "large",
	});

	let video = $(
		`<div class="video-player" data-plyr-provider="youtube" data-plyr-embed-id="${youtube_id}"></div>`
	);
	video.appendTo(dialog.body);

	dialog.show();
	dialog.$wrapper.addClass("video-modal");

	let plyr;
	saashq.utils.load_video_player().then(() => {
		plyr = new saashq.Plyr(video[0], {
			hideControls: true,
			resetOnEnd: true,
		});
	});

	dialog.onhide = () => {
		plyr?.destroy();
	};
};

$("body").on("click", "a.help-link", function () {
	var doctype = $(this).attr("data-doctype");
	doctype && saashq.help.show(doctype);
});
