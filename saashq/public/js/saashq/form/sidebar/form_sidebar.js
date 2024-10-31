import "./assign_to";
import "./attachments";
import "./share";
import "./review";
import "./document_follow";
import "./user_image";
import "./form_sidebar_users";
import { get_user_link, get_user_message } from "../footer/version_timeline_content_builder";

saashq.ui.form.Sidebar = class {
	constructor(opts) {
		$.extend(this, opts);
	}

	make() {
		var sidebar_content = saashq.render_template("form_sidebar", {
			doctype: this.frm.doctype,
			frm: this.frm,
			can_write: saashq.model.can_write(this.frm.doctype, this.frm.docname),
		});

		this.sidebar = $('<div class="form-sidebar overlay-sidebar hidden-xs hidden-sm"></div>')
			.html(sidebar_content)
			.appendTo(this.page.sidebar.empty());

		this.user_actions = this.sidebar.find(".user-actions");
		this.image_section = this.sidebar.find(".sidebar-image-section");
		this.image_wrapper = this.image_section.find(".sidebar-image-wrapper");
		this.make_assignments();
		this.make_attachments();
		this.make_review();
		this.make_shared();

		this.make_tags();

		this.setup_keyboard_shortcuts();
		this.show_auto_repeat_status();
		this.show_error_log_status();
		this.show_webhook_request_log_status();
		saashq.ui.form.setup_user_image_event(this.frm);

		this.refresh();
	}

	setup_keyboard_shortcuts() {
		// add assignment shortcut
		let assignment_link = this.sidebar.find(".add-assignment");
		saashq.ui.keys.get_shortcut_group(this.page).add(assignment_link);
	}

	refresh() {
		if (this.frm.doc.__islocal) {
			this.sidebar.toggle(false);
			this.page.sidebar.addClass("hide-sidebar");
		} else {
			this.page.sidebar.removeClass("hide-sidebar");
			this.sidebar.toggle(true);
			this.frm.assign_to.refresh();
			this.frm.attachments.refresh();
			this.frm.shared.refresh();

			this.frm.tags && this.frm.tags.refresh(this.frm.get_docinfo().tags);

			this.refresh_web_view_count();
			this.refresh_creation_modified();
			saashq.ui.form.set_user_image(this.frm);
		}
	}

	refresh_web_view_count() {
		if (this.frm.doc.route && cint(saashq.boot.website_tracking_enabled)) {
			let route = this.frm.doc.route;
			saashq.utils.get_page_view_count(route).then((res) => {
				this.sidebar
					.find(".pageview-count")
					.removeClass("hidden")
					.html(__("{0} Web page views", [String(res.message).bold()]));
			});
		}
	}

	refresh_creation_modified() {
		let user_list = [this.frm.doc.owner, this.frm.doc.modified_by];
		if (this.frm.doc.owner === this.frm.doc.modified_by) {
			user_list = [this.frm.doc.owner];
		}

		let avatar_group = saashq.avatar_group(user_list, 5, {
			align: "left",
			overlap: true,
		});

		this.sidebar.find(".created-modified-section").append(avatar_group);

		let creation_message =
			get_user_message(
				this.frm.doc.owner,
				__("You created this", null),
				__("{0} created this", [get_user_link(this.frm.doc.owner)])
			) +
			" · " +
			comment_when(this.frm.doc.creation);

		let modified_message =
			get_user_message(
				this.frm.doc.modified_by,
				__("You last edited this", null),
				__("{0} last edited this", [get_user_link(this.frm.doc.modified_by)])
			) +
			" · " +
			comment_when(this.frm.doc.modified);

		if (user_list.length === 1) {
			// same user created and edited

			avatar_group.find(".avatar").popover({
				trigger: "hover",
				html: true,
				content: creation_message + "<br>" + modified_message,
			});
		} else {
			avatar_group.find(".avatar:first-child").popover({
				trigger: "hover",
				html: true,
				content: creation_message,
			});

			avatar_group.find(".avatar:last-child").popover({
				trigger: "hover",
				html: true,
				content: modified_message,
			});
		}
	}

	show_auto_repeat_status() {
		if (this.frm.meta.allow_auto_repeat && this.frm.doc.auto_repeat) {
			const me = this;
			saashq.call({
				method: "saashq.client.get_value",
				args: {
					doctype: "Auto Repeat",
					filters: {
						name: this.frm.doc.auto_repeat,
					},
					fieldname: ["frequency"],
				},
				callback: function (res) {
					let el = me.sidebar.find(".auto-repeat-status");
					el.find("span").html(__("Repeats {0}", [__(res.message.frequency)]));
					el.closest(".sidebar-section").removeClass("hidden");
					el.show();
					el.on("click", function () {
						saashq.set_route("Form", "Auto Repeat", me.frm.doc.auto_repeat);
					});
				},
			});
		}
	}

	show_error_log_status() {
		const docinfo = this.frm.get_docinfo();
		if (docinfo.error_log_exists) {
			let el = this.sidebar.find(".error-log-status");
			el.closest(".sidebar-section").removeClass("hidden");
			el.show();
			el.on("click", () => {
				saashq.set_route("List", "Error Log", {
					reference_doctype: this.frm.doc.doctype,
					reference_name: this.frm.doc.name,
				});
			});
		}
	}

	show_webhook_request_log_status() {
		const docinfo = this.frm.get_docinfo();
		if (docinfo.webhook_request_log_exists) {
			let el = this.sidebar.find(".webhook-request-log-status");
			el.closest(".sidebar-section").removeClass("hidden");
			el.show();
			el.on("click", () => {
				saashq.set_route("List", "Webhook Request Log", {
					reference_doctype: this.frm.doc.doctype,
					reference_document: this.frm.doc.name,
				});
			});
		}
	}

	make_tags() {
		if (this.frm.meta.issingle) {
			this.sidebar.find(".form-tags").toggle(false);
			return;
		}

		let tags_parent = this.sidebar.find(".form-tags");

		this.frm.tags = new saashq.ui.TagEditor({
			parent: tags_parent,
			add_button: tags_parent.find(".add-tags-btn"),
			frm: this.frm,
			on_change: function (user_tags) {
				this.frm.tags && this.frm.tags.refresh(user_tags);
			},
		});
	}

	make_attachments() {
		var me = this;
		this.frm.attachments = new saashq.ui.form.Attachments({
			parent: me.sidebar.find(".form-attachments"),
			frm: me.frm,
		});
	}

	make_assignments() {
		this.frm.assign_to = new saashq.ui.form.AssignTo({
			parent: this.sidebar.find(".form-assignments"),
			frm: this.frm,
		});
	}

	make_shared() {
		this.frm.shared = new saashq.ui.form.Share({
			frm: this.frm,
			parent: this.sidebar.find(".form-shared"),
		});
	}

	add_user_action(label, click) {
		return $("<a>")
			.html(label)
			.appendTo(
				$('<div class="user-action-row"></div>').appendTo(
					this.user_actions.removeClass("hidden")
				)
			)
			.on("click", click);
	}

	clear_user_actions() {
		this.user_actions.addClass("hidden");
		this.user_actions.find(".user-action-row").remove();
	}

	refresh_image() {}

	make_review() {
		const review_wrapper = this.sidebar.find(".form-reviews");
		if (saashq.boot.energy_points_enabled && !this.frm.is_new()) {
			this.frm.reviews = new saashq.ui.form.Review({
				parent: review_wrapper,
				frm: this.frm,
			});
		} else {
			review_wrapper.remove();
		}
	}

	reload_docinfo(callback) {
		saashq.call({
			method: "saashq.desk.form.load.get_docinfo",
			args: {
				doctype: this.frm.doctype,
				name: this.frm.docname,
			},
			callback: (r) => {
				// docinfo will be synced
				if (callback) callback(r.docinfo);
				this.frm.timeline && this.frm.timeline.refresh();
				this.frm.assign_to.refresh();
				this.frm.attachments.refresh();
			},
		});
	}
};
