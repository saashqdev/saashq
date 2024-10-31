// Copyleft (l) 2023-Present, SaasHQ
// MIT License. See license.txt

saashq.provide("saashq.model");

$.extend(saashq.model, {
	new_names: {},

	get_new_doc: function (doctype, parent_doc, parentfield, with_mandatory_children) {
		saashq.provide("locals." + doctype);
		var doc = {
			docstatus: 0,
			doctype: doctype,
			name: saashq.model.get_new_name(doctype),
			__islocal: 1,
			__unsaved: 1,
			owner: saashq.session.user,
		};
		saashq.model.set_default_values(doc, parent_doc);

		if (parent_doc) {
			$.extend(doc, {
				parent: parent_doc.name,
				parentfield: parentfield,
				parenttype: parent_doc.doctype,
			});
			if (!parent_doc[parentfield]) parent_doc[parentfield] = [];
			doc.idx = parent_doc[parentfield].length + 1;
			parent_doc[parentfield].push(doc);
		} else {
			saashq.provide("saashq.model.docinfo." + doctype + "." + doc.name);
		}

		saashq.model.add_to_locals(doc);

		if (with_mandatory_children) {
			saashq.model.create_mandatory_children(doc);
		}

		if (!parent_doc) {
			doc.__run_link_triggers = 1;
		}

		// set the name if called from a link field
		if (saashq.route_options && saashq.route_options.name_field) {
			var meta = saashq.get_meta(doctype);
			// set title field / name as name
			if (meta.autoname && meta.autoname.indexOf("field:") !== -1) {
				doc[meta.autoname.substr(6)] = saashq.route_options.name_field;
			} else if (meta.autoname && meta.autoname === "prompt") {
				doc.__newname = saashq.route_options.name_field;
			} else if (meta.title_field) {
				doc[meta.title_field] = saashq.route_options.name_field;
			}

			delete saashq.route_options.name_field;
		}

		// set route options
		if (saashq.route_options && !doc.parent) {
			$.each(saashq.route_options, function (fieldname, value) {
				var df = saashq.meta.has_field(doctype, fieldname);
				if (
					df &&
					["Link", "Data", "Select", "Dynamic Link"].includes(df.fieldtype) &&
					!df.no_copy
				) {
					doc[fieldname] = value;
				}
			});
			saashq.route_options = null;
		}

		return doc;
	},

	make_new_doc_and_get_name: function (doctype, with_mandatory_children) {
		return saashq.model.get_new_doc(doctype, null, null, with_mandatory_children).name;
	},

	get_new_name: function (doctype) {
		// random hash is added to idenity mislinked files when doc is not saved and file is uploaded.
		return saashq.router.slug(`new-${doctype}-${saashq.utils.get_random(10)}`);
	},

	set_default_values: function (doc, parent_doc) {
		let doctype = doc.doctype;
		let docfields = saashq.meta.get_docfields(doctype);
		let updated = [];

		// Table types should be initialized
		let fieldtypes_without_default = saashq.model.no_value_type.filter(
			(fieldtype) => !saashq.model.table_fields.includes(fieldtype)
		);
		docfields.forEach((f) => {
			if (
				fieldtypes_without_default.includes(f.fieldtype) ||
				doc[f.fieldname] != null ||
				f.no_default
			) {
				return;
			}

			let v = saashq.model.get_default_value(f, doc, parent_doc);
			if (v) {
				if (["Int", "Check"].includes(f.fieldtype)) v = cint(v);
				else if (["Currency", "Float"].includes(f.fieldtype)) v = flt(v);

				doc[f.fieldname] = v;
				updated.push(f.fieldname);
			} else if (
				f.fieldtype == "Select" &&
				f.options &&
				typeof f.options === "string" &&
				!["[Select]", "Loading..."].includes(f.options)
			) {
				doc[f.fieldname] = f.options.split("\n")[0];
			}
		});
		return updated;
	},

	create_mandatory_children: function (doc) {
		var meta = saashq.get_meta(doc.doctype);
		if (meta && meta.istable) return;

		// create empty rows for mandatory table fields
		saashq.meta.get_docfields(doc.doctype).forEach(function (df) {
			if (df.fieldtype === "Table" && df.reqd) {
				saashq.model.add_child(doc, df.fieldname);
			}
		});
	},

	get_default_value: function (df, doc, parent_doc) {
		var user_default = "";
		var user_permissions = saashq.defaults.get_user_permissions();
		let allowed_records = [];
		let default_doc = null;
		let value = null;
		if (user_permissions) {
			({ allowed_records, default_doc } = saashq.perm.filter_allowed_docs_for_doctype(
				user_permissions[df.options],
				doc.doctype
			));
		}
		var meta = saashq.get_meta(doc.doctype);
		var has_user_permissions =
			df.fieldtype === "Link" &&
			!$.isEmptyObject(user_permissions) &&
			df.ignore_user_permissions != 1 &&
			allowed_records.length;

		// don't set defaults for "User" link field using User Permissions!
		if (df.fieldtype === "Link" && df.options !== "User") {
			// If user permission has Is Default enabled or single-user permission has found against respective doctype.
			if (has_user_permissions && default_doc) {
				value = default_doc;
			} else {
				// 2 - look in user defaults

				if (!df.ignore_user_permissions) {
					var user_defaults = saashq.defaults.get_user_defaults(df.options);
					if (user_defaults && user_defaults.length === 1) {
						// Use User Permission value when only when it has a single value
						user_default = user_defaults[0];
					}
				}

				if (!user_default) {
					user_default = saashq.defaults.get_user_default(df.fieldname);
				}
				if (
					!user_default &&
					df.remember_last_selected_value &&
					saashq.boot.user.last_selected_values
				) {
					user_default = saashq.boot.user.last_selected_values[df.options];
				}

				var is_allowed_user_default =
					user_default &&
					(!has_user_permissions || allowed_records.includes(user_default));

				// is this user default also allowed as per user permissions?
				if (is_allowed_user_default) {
					value = user_default;
				}
			}
		}

		// 3 - look in default of docfield
		if (!value || df["default"]) {
			const default_val = String(df["default"]);
			if (default_val == "__user" || default_val.toLowerCase() == "user") {
				value = saashq.session.user;
			} else if (default_val == "user_fullname") {
				value = saashq.session.user_fullname;
			} else if (default_val == "Today") {
				value = saashq.datetime.get_today();
			} else if ((default_val || "").toLowerCase() === "now") {
				if (df.fieldtype == "Time") {
					value = saashq.datetime.now_time();
				} else {
					// datetime fields are stored in system tz
					value = saashq.datetime.system_datetime();
				}
			} else if (default_val[0] === ":") {
				var boot_doc = saashq.model.get_default_from_boot_docs(df, doc, parent_doc);
				var is_allowed_boot_doc =
					!has_user_permissions || allowed_records.includes(boot_doc);

				if (is_allowed_boot_doc) {
					value = boot_doc;
				}
			} else if (df.fieldname === meta.title_field) {
				// ignore defaults for title field
				value = "";
			} else {
				// is this default value is also allowed as per user permissions?
				var is_allowed_default =
					!has_user_permissions || allowed_records.includes(df.default);
				if (df.fieldtype !== "Link" || df.options === "User" || is_allowed_default) {
					value = df["default"];
				}
			}
		} else if (df.fieldtype == "Time") {
			value = saashq.datetime.now_time();
		}

		if (saashq.model.table_fields.includes(df.fieldtype)) {
			value = [];
		}

		// set it here so we know it was set as a default
		df.__default_value = value;

		return value;
	},

	get_default_from_boot_docs: function (df, doc, parent_doc) {
		// set default from partial docs passed during boot like ":User"
		if (saashq.get_list(df["default"]).length > 0) {
			var ref_fieldname = df["default"].slice(1).toLowerCase().replace(" ", "_");
			var ref_value = parent_doc
				? parent_doc[ref_fieldname]
				: saashq.defaults.get_user_default(ref_fieldname);
			var ref_doc = ref_value ? saashq.get_doc(df["default"], ref_value) : null;

			if (ref_doc && ref_doc[df.fieldname]) {
				return ref_doc[df.fieldname];
			}
		}
	},

	add_child: function (parent_doc, doctype, parentfield, idx) {
		// if given doc, fieldname only
		if (arguments.length === 2) {
			parentfield = doctype;
			doctype = saashq.meta.get_field(parent_doc.doctype, parentfield).options;
		}

		// create row doc
		idx = idx ? idx - 0.1 : (parent_doc[parentfield] || []).length + 1;

		var child = saashq.model.get_new_doc(doctype, parent_doc, parentfield);
		child.idx = idx;

		// renum for fraction
		if (idx !== cint(idx)) {
			var sorted = parent_doc[parentfield].sort(function (a, b) {
				return a.idx - b.idx;
			});
			for (var i = 0, j = sorted.length; i < j; i++) {
				var d = sorted[i];
				d.idx = i + 1;
			}
		}

		if (cur_frm && cur_frm.doc == parent_doc) cur_frm.dirty();

		return child;
	},

	copy_doc: function (doc, from_amend, parent_doc, parentfield) {
		var no_copy_list = ["name", "amended_from", "amendment_date", "cancel_reason"];
		var newdoc = saashq.model.get_new_doc(doc.doctype, parent_doc, parentfield);

		for (var key in doc) {
			// dont copy name and blank fields
			var df = saashq.meta.get_docfield(doc.doctype, key);

			if (
				df &&
				key.substr(0, 2) != "__" &&
				!no_copy_list.includes(key) &&
				!(df && !from_amend && cint(df.no_copy) == 1)
			) {
				var value = doc[key] || [];
				if (saashq.model.table_fields.includes(df.fieldtype)) {
					for (var i = 0, j = value.length; i < j; i++) {
						var d = value[i];
						saashq.model.copy_doc(d, from_amend, newdoc, df.fieldname);
					}
				} else {
					newdoc[key] = doc[key];
				}
			}
		}

		var user = saashq.session.user;

		newdoc.__islocal = 1;
		newdoc.docstatus = 0;
		newdoc.owner = user;
		newdoc.creation = "";
		newdoc.modified_by = user;
		newdoc.modified = "";
		newdoc.lft = null;
		newdoc.rgt = null;

		if (from_amend && parent_doc) {
			newdoc._amended_from = doc.name;
		}

		return newdoc;
	},

	open_mapped_doc: function (opts) {
		if (opts.frm && opts.frm.doc.__unsaved) {
			saashq.throw(
				__("You have unsaved changes in this form. Please save before you continue.")
			);
		} else if (!opts.source_name && opts.frm) {
			opts.source_name = opts.frm.doc.name;
		} else if (!opts.frm && !opts.source_name) {
			opts.source_name = null;
		}

		return saashq.call({
			type: "POST",
			method: "saashq.model.mapper.make_mapped_doc",
			args: {
				method: opts.method,
				source_name: opts.source_name,
				args: opts.args || null,
				selected_children: opts.frm ? opts.frm.get_selected() : null,
			},
			freeze: true,
			freeze_message: opts.freeze_message || "",
			callback: function (r) {
				if (!r.exc) {
					saashq.model.sync(r.message);
					if (opts.run_link_triggers) {
						saashq.get_doc(
							r.message.doctype,
							r.message.name
						).__run_link_triggers = true;
					}
					saashq.set_route("Form", r.message.doctype, r.message.name);
				}
			},
		});
	},
});

saashq.create_routes = {};
saashq.new_doc = function (doctype, opts, init_callback) {
	if (doctype === "File") {
		new saashq.ui.FileUploader({
			folder: opts ? opts.folder : "Home",
		});
		return;
	}
	return new Promise((resolve) => {
		if (opts && $.isPlainObject(opts)) {
			saashq.route_options = opts;
		}
		saashq.model.with_doctype(doctype, function () {
			if (saashq.create_routes[doctype]) {
				saashq.set_route(saashq.create_routes[doctype]).then(() => resolve());
			} else {
				saashq.ui.form
					.make_quick_entry(doctype, null, init_callback)
					.then(() => resolve());
			}
		});
	});
};
