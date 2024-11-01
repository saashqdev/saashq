// Copyright (c) 2023-Present, SaasHQ
// MIT License. See license.txt

saashq.provide("saashq.ui.form");

saashq.ui.form.DocumentFollow = class DocumentFollow {
	constructor(opts) {
		$.extend(this, opts);
		if (!saashq.boot.user.document_follow_notify) {
			this.hide_follow_section();
			return;
		}
		this.follow_document_link = this.parent.find(".follow-document-link");
		this.unfollow_document_link = this.parent.find(".unfollow-document-link");
		this.follow_span = this.parent.find(".anchor-document-follow > span");
		this.followed_by = this.parent.find(".followed-by");
		this.followed_by_label = this.parent.find(".followed-by-label");
	}

	refresh() {
		this.set_followers();
		this.render_sidebar();
	}

	render_sidebar() {
		const docinfo = this.frm.get_docinfo();
		const document_follow_enabled = saashq.boot.user.document_follow_notify;
		const document_can_be_followed = saashq.get_meta(this.frm.doctype).track_changes;
		if (
			saashq.session.user === "Administrator" ||
			!document_follow_enabled ||
			!document_can_be_followed
		) {
			this.hide_follow_section();
			return;
		}
		this.bind_events();

		const is_followed = docinfo && docinfo.is_document_followed;

		if (is_followed > 0) {
			this.unfollow_document_link.removeClass("hidden");
			this.follow_document_link.addClass("hidden");
		} else {
			this.followed_by_label.addClass("hidden");
			this.followed_by.addClass("hidden");
			this.unfollow_document_link.addClass("hidden");
			this.follow_document_link.removeClass("hidden");
		}
	}

	bind_events() {
		this.follow_document_link.on("click", () => {
			this.follow_document_link.addClass("text-muted disable-click");
			saashq.call({
				method: "saashq.desk.form.document_follow.follow_document",
				args: {
					doctype: this.frm.doctype,
					doc_name: this.frm.doc.name,
					user: saashq.session.user,
					force: true,
				},
				callback: (r) => {
					if (r.message) {
						this.follow_action();
					}
				},
			});
		});

		this.unfollow_document_link.on("click", () => {
			this.unfollow_document_link.addClass("text-muted disable-click");
			saashq.call({
				method: "saashq.desk.form.document_follow.unfollow_document",
				args: {
					doctype: this.frm.doctype,
					doc_name: this.frm.doc.name,
					user: saashq.session.user,
				},
				callback: (r) => {
					if (r.message) {
						this.unfollow_action();
					}
				},
			});
		});
	}

	hide_follow_section() {
		this.parent.addClass("hidden");
	}

	set_followers() {
		this.parent.removeClass("hidden");
		this.followed_by_label.removeClass("hidden");
		this.followed_by.empty();
		this.get_followed_user().then((user) => {
			$(user).appendTo(this.followed_by);
		});
	}

	get_followed_user() {
		var html = "";
		return new Promise((resolve) => {
			saashq
				.call({
					method: "saashq.desk.form.document_follow.get_follow_users",
					args: {
						doctype: this.frm.doctype,
						doc_name: this.frm.doc.name,
					},
				})
				.then((r) => {
					this.count_others = 0;
					for (var d in r.message) {
						this.count_others++;
						if (this.count_others < 4) {
							html += saashq.avatar(r.message[d].user, "avatar-small");
						}
						if (this.count_others === 0) {
							this.followed_by.addClass("hidden");
						}
					}
					resolve(html);
				});
		});
	}

	follow_action() {
		saashq.show_alert({
			message: __(
				"You are now following this document. You will receive daily updates via email. You can change this in User Settings."
			),
			indicator: "orange",
		});
		this.follow_document_link.removeClass("text-muted disable-click");
		this.follow_document_link.addClass("hidden");
		this.unfollow_document_link.removeClass("hidden");
		this.set_followers();
	}

	unfollow_action() {
		saashq.show_alert({
			message: __("You unfollowed this document"),
			indicator: "red",
		});
		this.unfollow_document_link.removeClass("text-muted disable-click");
		this.unfollow_document_link.addClass("hidden");
		this.follow_document_link.removeClass("hidden");
		this.followed_by.addClass("hidden");
		this.followed_by_label.addClass("hidden");
	}
};
