// Copyright (c) 2023-Present, SaasHQ
// MIT License. See license.txt

saashq.ui.form.AssignTo = class AssignTo {
	constructor(opts) {
		$.extend(this, opts);
		this.btn = this.parent.find(".add-assignment-btn").on("click", () => this.add());
		this.btn_wrapper = this.btn.parent();

		this.refresh();
	}
	refresh() {
		if (this.frm.doc.__islocal) {
			this.parent.toggle(false);
			return;
		}
		this.parent.toggle(true);
		this.render(this.frm.get_docinfo().assignments);
	}
	render(assignments) {
		this.frm.get_docinfo().assignments = assignments;

		let assignments_wrapper = this.parent.find(".assignments");

		assignments_wrapper.empty();
		let assigned_users = assignments.map((d) => d.owner);

		if (!assigned_users.length) {
			assignments_wrapper.hide();
			return;
		}

		let avatar_group = saashq.avatar_group(assigned_users, 5, {
			align: "left",
			overlap: true,
		});

		assignments_wrapper.show();
		assignments_wrapper.append(avatar_group);
		avatar_group.click(() => {
			new saashq.ui.form.AssignmentDialog({
				assignments: assigned_users,
				frm: this.frm,
			});
		});
	}
	add() {
		var me = this;

		if (this.frm.is_new()) {
			saashq.throw(__("Please save the document before assignment"));
			return;
		}

		if (!me.assign_to) {
			me.assign_to = new saashq.ui.form.AssignToDialog({
				method: "saashq.desk.form.assign_to.add",
				doctype: me.frm.doctype,
				docname: me.frm.docname,
				frm: me.frm,
				callback: function (r) {
					me.render(r.message);
				},
			});
		}
		me.assign_to.dialog.clear();
		me.assign_to.dialog.show();
	}
	remove(owner) {
		if (this.frm.is_new()) {
			saashq.throw(__("Please save the document before removing assignment"));
			return;
		}

		return saashq
			.xcall("saashq.desk.form.assign_to.remove", {
				doctype: this.frm.doctype,
				name: this.frm.docname,
				assign_to: owner,
			})
			.then((assignments) => {
				this.render(assignments);
			});
	}
};

saashq.ui.form.AssignToDialog = class AssignToDialog {
	constructor(opts) {
		$.extend(this, opts);

		this.make();
		this.set_description_from_doc();
	}
	make() {
		let me = this;

		me.dialog = new saashq.ui.Dialog({
			title: __("Add to ToDo"),
			fields: me.get_fields(),
			primary_action_label: __("Add"),
			primary_action: function () {
				let args = me.dialog.get_values();

				if (args && args.assign_to) {
					me.dialog.set_message("Assigning...");

					saashq.call({
						method: me.method,
						args: $.extend(args, {
							doctype: me.doctype,
							name: me.docname,
							assign_to: args.assign_to,
							bulk_assign: me.bulk_assign || false,
							re_assign: me.re_assign || false,
						}),
						btn: me.dialog.get_primary_btn(),
						callback: function (r) {
							if (!r.exc) {
								if (me.callback) {
									me.callback(r);
								}
								me.dialog && me.dialog.hide();
							} else {
								me.dialog.clear_message();
							}
						},
					});
				}
			},
		});
	}
	assign_to_me() {
		let me = this;
		let assign_to = [];

		if (me.dialog.get_value("assign_to_me")) {
			assign_to.push(saashq.session.user);
		}

		me.dialog.set_value("assign_to", assign_to);
	}
	user_group_list() {
		let me = this;
		let user_group = me.dialog.get_value("assign_to_user_group");
		me.dialog.set_value("assign_to_me", 0);

		if (user_group) {
			let user_group_members = [];
			saashq.db
				.get_list("User Group Member", {
					parent_doctype: "User Group",
					filters: { parent: user_group },
					fields: ["user"],
				})
				.then((response) => {
					user_group_members = response.map((group_member) => group_member.user);
					me.dialog.set_value("assign_to", user_group_members);
				});
		}
	}
	set_description_from_doc() {
		let me = this;

		if (me.frm && me.frm.meta.title_field) {
			me.dialog.set_value("description", me.frm.doc[me.frm.meta.title_field]);
		}
	}
	get_fields() {
		let me = this;

		return [
			{
				label: __("Assign to me"),
				fieldtype: "Check",
				fieldname: "assign_to_me",
				default: 0,
				onchange: () => me.assign_to_me(),
			},
			{
				label: __("Assign To User Group"),
				fieldtype: "Link",
				fieldname: "assign_to_user_group",
				options: "User Group",
				onchange: () => me.user_group_list(),
			},
			{
				fieldtype: "MultiSelectPills",
				fieldname: "assign_to",
				label: __("Assign To"),
				reqd: true,
				get_data: function (txt) {
					return saashq.db.get_link_options("User", txt, {
						user_type: "System User",
						enabled: 1,
					});
				},
			},
			{
				fieldtype: "Section Break",
			},
			{
				label: __("Complete By"),
				fieldtype: "Date",
				fieldname: "date",
			},
			{
				fieldtype: "Column Break",
			},
			{
				label: __("Priority"),
				fieldtype: "Select",
				fieldname: "priority",
				options: [
					{
						value: "Low",
						label: __("Low"),
					},
					{
						value: "Medium",
						label: __("Medium"),
					},
					{
						value: "High",
						label: __("High"),
					},
				],
				// Pick up priority from the source document, if it exists and is available in ToDo
				default: ["Low", "Medium", "High"].includes(
					me.frm && me.frm.doc.priority ? me.frm.doc.priority : "Medium"
				),
			},
			{
				fieldtype: "Section Break",
			},
			{
				label: __("Comment"),
				fieldtype: "Small Text",
				fieldname: "description",
			},
		];
	}
};

saashq.ui.form.AssignmentDialog = class {
	constructor(opts) {
		this.frm = opts.frm;
		this.assignments = opts.assignments;
		this.make();
	}

	make() {
		this.dialog = new saashq.ui.Dialog({
			title: __("Assignments"),
			size: "small",
			no_focus: true,
			fields: [
				{
					label: __("Assign a user"),
					fieldname: "user",
					fieldtype: "Link",
					options: "User",
					change: () => {
						let value = this.dialog.get_value("user");
						if (value && !this.assigning) {
							this.assigning = true;
							this.dialog.set_df_property("user", "read_only", 1);
							this.dialog.set_df_property("user", "description", __("Assigning..."));
							this.add_assignment(value)
								.then(() => {
									this.dialog.set_value("user", null);
								})
								.finally(() => {
									this.dialog.set_df_property("user", "description", null);
									this.dialog.set_df_property("user", "read_only", 0);
									this.assigning = false;
								});
						}
					},
				},
				{
					fieldtype: "HTML",
					fieldname: "assignment_list",
				},
			],
		});

		this.assignment_list = $(this.dialog.get_field("assignment_list").wrapper);
		this.assignment_list.removeClass("saashq-control");

		this.assignments.forEach((assignment) => {
			this.update_assignment(assignment);
		});
		this.dialog.show();
	}
	render(assignments) {
		this.frm && this.frm.assign_to.render(assignments);
	}
	add_assignment(assignment) {
		return saashq
			.xcall("saashq.desk.form.assign_to.add", {
				doctype: this.frm.doctype,
				name: this.frm.docname,
				assign_to: [assignment],
			})
			.then((assignments) => {
				this.update_assignment(assignment);
				this.render(assignments);
			});
	}
	remove_assignment(assignment) {
		return saashq.xcall("saashq.desk.form.assign_to.remove", {
			doctype: this.frm.doctype,
			name: this.frm.docname,
			assign_to: assignment,
		});
	}
	close_assignment(assignment) {
		return saashq.xcall("saashq.desk.form.assign_to.close", {
			doctype: this.frm.doctype,
			name: this.frm.docname,
			assign_to: assignment,
		});
	}
	update_assignment(assignment) {
		const in_the_list = this.assignment_list.find(`[data-user="${assignment}"]`).length;
		if (!in_the_list) {
			this.assignment_list.append(this.get_assignment_row(assignment));
		}
	}
	get_assignment_row(assignment) {
		const row = $(`
			<div class="dialog-assignment-row" data-user="${assignment}">
				<div class="assignee">
					${saashq.avatar(assignment)}
					${saashq.user.full_name(assignment)}
				</div>
				<div class="btn-group btn-group-sm" role="group" aria-label="Actions">
				</div>
			</div>
		`);

		const btn_group = row.find(".btn-group");

		if (assignment === saashq.session.user) {
			btn_group.append(`
				<button type="button" class="btn btn-default complete-btn" title="${__("Done")}">
					${saashq.utils.icon("tick", "xs")}
				</button>
			`);
			btn_group.find(".complete-btn").click(() => {
				this.close_assignment(assignment).then((assignments) => {
					row.remove();
					this.render(assignments);
				});
			});
		}

		if (assignment === saashq.session.user || this.frm.perm[0].write) {
			btn_group.append(`
				<button type="button" class="btn btn-default remove-btn" title="${__("Cancel")}">
				${saashq.utils.icon("close")}
				</button>
			`);
			btn_group.find(".remove-btn").click(() => {
				this.remove_assignment(assignment).then((assignments) => {
					row.remove();
					this.render(assignments);
				});
			});
		}
		return row;
	}
};
