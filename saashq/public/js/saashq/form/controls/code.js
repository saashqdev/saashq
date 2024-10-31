saashq.ui.form.ControlCode = class ControlCode extends saashq.ui.form.ControlText {
	make_input() {
		if (this.editor) return;
		this.load_lib().then(() => this.make_ace_editor());
	}

	refresh() {
		super.refresh();
		if (this.df.fieldtype === "Code") {
			// Don't show for derived classes
			this.setup_copy_button();
		}
	}

	setup_copy_button() {
		if (this.get_status() === "Write") {
			this.copy_button?.remove();
			this.copy_button = null;
			return; // Don't show copy button in write mode
		}

		if (this.copy_button) {
			return;
		}

		this.copy_button = $(
			`<button
				class="btn icon-btn"
				style="position: absolute; top: 32px; right: 5px;"
				onmouseover="this.classList.add('btn-default')"
				onmouseout="this.classList.remove('btn-default')"
			>
				<svg class="es-icon es-line  icon-sm" style="" aria-hidden="true">
					<use class="" href="#es-line-copy-light"></use>
				</svg>
			</button>`
		);
		this.copy_button.on("click", () => {
			saashq.utils.copy_to_clipboard(this.get_model_value() || this.get_value());
		});
		this.copy_button.appendTo(this.$wrapper);
	}

	make_ace_editor() {
		if (this.editor) return;
		this.ace_editor_target = $('<div class="ace-editor-target"></div>').appendTo(
			this.input_area
		);

		// styling
		this.ace_editor_target.addClass("border rounded");
		this.ace_editor_target.css("height", 300);

		if (this.df.max_height) {
			this.ace_editor_target.css("max-height", this.df.max_height);
		}

		// initialize
		const ace = window.ace;
		this.editor = ace.edit(this.ace_editor_target.get(0));

		if (this.df.max_lines || this.df.min_lines || this.df.max_height) {
			if (this.df.max_lines) this.editor.setOption("maxLines", this.df.max_lines);
			if (this.df.min_lines) this.editor.setOption("minLines", this.df.min_lines);
		} else {
			this.expanded = false;
			this.$expand_button = $(
				`<button class="btn btn-xs btn-default mt-2">${this.get_button_label()}</button>`
			)
				.click(() => {
					this.expanded = !this.expanded;
					this.refresh_height();
					this.toggle_label();
				})
				.appendTo(this.$input_wrapper);
		}

		if (this.disabled) {
			this.editor.setReadOnly(true);
			$(this.ace_editor_target).css("pointer-events", "none");
		}

		this.editor.setTheme("ace/theme/tomorrow");
		this.editor.setOption("showPrintMargin", false);
		this.editor.setOption("wrap", this.df.wrap);
		this.set_language();
		this.is_setting_content = false;

		// events
		this.editor.session.on("change", () => {
			if (this.is_setting_content) return;
			change_content();
		});

		let change_content = saashq.utils.debounce(() => {
			const input_value = this.get_input_value();
			this.parse_validate_and_set_in_model(input_value);
		}, 300);

		// setup autocompletion when it is set the first time
		Object.defineProperty(this.df, "autocompletions", {
			configurable: true,
			get() {
				return this._autocompletions || [];
			},
			set: (value) => {
				let getter = value;
				if (typeof getter !== "function") {
					getter = () => value;
				}
				if (!this._autocompletions) {
					this._autocompletions = [];
				}
				this._autocompletions.push(getter);
				this.setup_autocompletion();
			},
		});
	}

	setup_autocompletion(customGetCompletions) {
		if (this._autocompletion_setup) return;

		const ace = window.ace;

		let getCompletions = (editor, session, pos, prefix, callback) => {
			if (prefix.length === 0) {
				callback(null, []);
				return;
			}
			const get_autocompletions = () => {
				let getters = this._autocompletions || [];
				let completions = [];
				for (let getter of getters) {
					let values = getter({ editor, session, pos, prefix });
					completions.push(...values);
				}
				return completions;
			};
			let autocompletions = get_autocompletions();
			if (autocompletions.length) {
				callback(
					null,
					autocompletions.map((a) => {
						if (typeof a === "string") {
							a = { value: a };
						}
						return {
							name: "saashq",
							value: a.value,
							score: a.score,
							meta: a.meta,
							caption: a.caption,
						};
					})
				);
			}
		};

		ace.config.loadModule("ace/ext/language_tools", (langTools) => {
			this.editor.setOptions({
				enableBasicAutocompletion: true,
				enableLiveAutocompletion: true,
			});

			langTools.addCompleter({
				getCompletions: customGetCompletions || getCompletions,
			});
		});
		this._autocompletion_setup = true;
	}

	refresh_height() {
		this.ace_editor_target.css("height", this.expanded ? 600 : 300);
		this.editor.resize();
	}

	toggle_label() {
		this.$expand_button && this.$expand_button.text(this.get_button_label());
	}

	get_button_label() {
		return this.expanded
			? __("Collapse", null, "Shrink code field.")
			: __("Expand", null, "Enlarge code field.");
	}

	set_language() {
		const language_map = {
			Javascript: "ace/mode/javascript",
			JS: "ace/mode/javascript",
			Python: "ace/mode/python",
			Py: "ace/mode/python",
			PythonExpression: "ace/mode/python",
			HTML: "ace/mode/html",
			CSS: "ace/mode/css",
			Markdown: "ace/mode/markdown",
			SCSS: "ace/mode/scss",
			JSON: "ace/mode/json",
			Golang: "ace/mode/golang",
			Go: "ace/mode/golang",
			Jinja: "ace/mode/django",
			SQL: "ace/mode/sql",
		};
		const language = this.df.options;

		const valid_languages = Object.keys(language_map);
		if (language && !valid_languages.includes(language)) {
			console.warn(
				`Invalid language option provided for field "${
					this.df.label
				}". Valid options are ${valid_languages.join(", ")}.`
			);
		}

		const ace_language_mode = language_map[language] || "";
		this.editor.session.setMode(ace_language_mode);
		this.editor.setKeyboardHandler(
			`ace/keyboard/${saashq.boot.user.code_editor_type || "vscode"}`
		);
	}

	parse(value) {
		if (value == null) {
			value = "";
		}
		return value;
	}

	set_formatted_input(value) {
		return this.load_lib().then(() => {
			if (!this.editor) return;
			if (!value) value = "";
			if (value === this.get_input_value()) return;
			this.is_setting_content = true;
			this.editor.session.setValue(value);
			this.is_setting_content = false;
		});
	}

	get_input_value() {
		return this.editor ? this.editor.session.getValue() : "";
	}

	load_lib() {
		if (this.library_loaded) return this.library_loaded;

		if (saashq.boot.developer_mode) {
			this.root_lib_path = "/assets/saashq/node_modules/ace-builds/src-noconflict/";
		} else {
			this.root_lib_path = "/assets/saashq/node_modules/ace-builds/src-min-noconflict/";
		}

		this.library_loaded = new Promise((resolve) => {
			saashq.require(this.root_lib_path + "ace.js", () => {
				window.ace.config.set("basePath", this.root_lib_path);
				resolve();
			});
		});

		return this.library_loaded;
	}
};
