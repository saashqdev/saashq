saashq.listview_settings["Recorder"] = {
	hide_name_column: true,

	onload(listview) {
		listview.page.sidebar.remove();
		if (!has_common(saashq.user_roles, ["Administrator", "System Manager"])) return;

		if (listview.list_view_settings) {
			listview.list_view_settings.disable_comment_count = true;
		}

		listview.page.add_button(__("Clear"), () => {
			saashq.xcall("saashq.recorder.delete").then(listview.refresh);
		});

		listview.page.add_menu_item(__("Import"), () => {
			new saashq.ui.FileUploader({
				folder: this.current_folder,
				on_success: (file) => {
					if (cur_list.data.length > 0) {
						// don't replace existing capture
						return;
					}
					saashq.call({
						method: "saashq.recorder.import_data",
						args: {
							file: file.file_url,
						},
						callback: function () {
							listview.refresh();
						},
					});
				},
			});
		});

		listview.page.add_menu_item(__("Export"), () => {
			saashq.call({
				method: "saashq.recorder.export_data",
				callback: function (r) {
					const data = r.message;
					const filename = `${data[0]["uuid"]}..${data[data.length - 1]["uuid"]}.json`;

					const el = document.createElement("a");
					el.setAttribute(
						"href",
						"data:application/json," + encodeURIComponent(JSON.stringify(data))
					);
					el.setAttribute("download", filename);
					el.click();
				},
			});
		});

		setInterval(() => {
			if (listview.list_view_settings.disable_auto_refresh) {
				return;
			}
			if (!listview.enabled) return;

			const route = saashq.get_route() || [];
			if (route[0] != "List" || "Recorder" != route[1]) {
				return;
			}

			listview.refresh();
		}, 5000);
	},

	refresh(listview) {
		this.fetch_recorder_status(listview).then(() => this.refresh_controls(listview));
	},

	refresh_controls(listview) {
		this.setup_recorder_controls(listview);
		this.update_indicators(listview);
	},

	fetch_recorder_status(listview) {
		return saashq.xcall("saashq.recorder.status").then((status) => {
			listview.enabled = Boolean(status);
		});
	},

	setup_recorder_controls(listview) {
		let me = this;
		listview.page.set_primary_action(listview.enabled ? __("Stop") : __("Start"), () => {
			if (listview.enabled) {
				me.stop_recorder(listview);
			} else {
				me.start_recorder(listview);
			}
		});
	},

	stop_recorder(listview) {
		let me = this;
		saashq.xcall("saashq.recorder.stop", {}).then(() => {
			listview.refresh();
			listview.enabled = false;
			me.refresh_controls(listview);
		});
	},

	start_recorder(listview) {
		let me = this;
		saashq.prompt(
			[
				{
					fieldtype: "Section Break",
					fieldname: "req_job_section",
				},
				{
					fieldtype: "Column Break",
					fieldname: "web_request_columns",
					label: "Web Requests",
				},
				{
					fieldname: "record_requests",
					fieldtype: "Check",
					label: "Record Web Requests",
					default: 1,
				},
				{
					fieldname: "request_filter",
					fieldtype: "Data",
					label: "Request path filter",
					default: "/",
					depends_on: "record_requests",
					description: `This will be used for filtering paths which will be recorded.
						You can use this to avoid slowing down other traffic.
						e.g. <code>/api/method/erpnexus</code>. Leave it empty to record every request.`,
				},
				{
					fieldtype: "Column Break",
					fieldname: "background_col",
					label: "Background Jobs",
				},

				{
					fieldname: "record_jobs",
					fieldtype: "Check",
					label: "Record Background Jobs",
					default: 1,
				},
				{
					fieldname: "jobs_filter",
					fieldtype: "Data",
					label: "Background Jobs filter",
					default: "",
					depends_on: "record_jobs",
					description: `This will be used for filtering jobs which will be recorded.
						You can use this to avoid slowing down other jobs. e.g. <code>email_queue.pull</code>.
						Leave it empty to record every job.`,
				},
				{
					fieldtype: "Section Break",
					fieldname: "sql_section",
					label: "SQL",
				},
				{
					fieldname: "record_sql",
					fieldtype: "Check",
					label: "Record SQL queries",
					default: 1,
				},
				{
					fieldname: "explain",
					fieldtype: "Check",
					label: "Generate EXPLAIN for SQL queries",
					default: 1,
				},
				{
					fieldname: "capture_stack",
					fieldtype: "Check",
					label: "Capture callstack of SQL queries",
					default: 1,
				},
				{
					fieldtype: "Section Break",
					fieldname: "python_section",
					label: "Python",
				},
				{
					fieldname: "profile",
					fieldtype: "Check",
					label: "Run cProfile",
					default: 0,
					description:
						"Warning: cProfile adds a lot of overhead. For best results, disable stack capturing when using cProfile.",
				},
			],
			(values) => {
				saashq.xcall("saashq.recorder.start", values).then(() => {
					listview.refresh();
					listview.enabled = true;
					me.refresh_controls(listview);
				});
			},
			__("Configure Recorder"),
			__("Start Recording")
		);
	},

	update_indicators(listview) {
		if (listview.enabled) {
			listview.page.set_indicator(__("Active"), "green");
		} else {
			listview.page.set_indicator(__("Inactive"), "red");
		}
	},
};
