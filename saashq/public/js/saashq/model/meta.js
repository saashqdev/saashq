// Copyleft (l) 2023-Present, SaasHQ
// MIT License. See license.txt

saashq.provide("saashq.meta.docfield_map");
saashq.provide("saashq.meta.docfield_copy");
saashq.provide("saashq.meta.docfield_list");
saashq.provide("saashq.meta.doctypes");
saashq.provide("saashq.meta.precision_map");

saashq.get_meta = function (doctype) {
	if (doctype === "DocType" && saashq.meta.__doctype_meta) {
		return saashq.meta.__doctype_meta;
	}
	return locals["DocType"] ? locals["DocType"][doctype] : null;
};

$.extend(saashq.meta, {
	sync: function (doc) {
		$.each(doc.fields, function (i, df) {
			saashq.meta.add_field(df);
		});

		if (doc.__print_formats?.length) saashq.model.sync(doc.__print_formats);
		if (doc.__workflow_docs?.length) saashq.model.sync(doc.__workflow_docs);
	},

	// build docfield_map and docfield_list
	add_field: function (df) {
		saashq.provide("saashq.meta.docfield_map." + df.parent);
		saashq.meta.docfield_map[df.parent][df.fieldname || df.label] = df;

		if (!saashq.meta.docfield_list[df.parent]) saashq.meta.docfield_list[df.parent] = [];

		// check for repeat
		for (var i in saashq.meta.docfield_list[df.parent]) {
			var d = saashq.meta.docfield_list[df.parent][i];
			if (df.fieldname == d.fieldname) return; // no repeat
		}
		saashq.meta.docfield_list[df.parent].push(df);
	},

	make_docfield_copy_for: function (doctype, docname, docfield_list = null) {
		var c = saashq.meta.docfield_copy;
		if (!c[doctype]) c[doctype] = {};
		if (!c[doctype][docname]) c[doctype][docname] = {};

		docfield_list = docfield_list || saashq.meta.docfield_list[doctype] || [];
		for (var i = 0, j = docfield_list.length; i < j; i++) {
			var df = docfield_list[i];
			c[doctype][docname][df.fieldname || df.label] = copy_dict(df);
		}
	},

	get_field: function (doctype, fieldname, name) {
		var out = saashq.meta.get_docfield(doctype, fieldname, name);

		// search in standard fields
		if (!out) {
			saashq.model.std_fields.every(function (d) {
				if (d.fieldname === fieldname) {
					out = d;
					return false;
				} else {
					return true;
				}
			});
		}
		return out;
	},

	get_docfield: function (doctype, fieldname, name) {
		var fields_dict = saashq.meta.get_docfield_copy(doctype, name);
		return fields_dict ? fields_dict[fieldname] : null;
	},

	set_formatter: function (doctype, fieldname, name, formatter) {
		saashq.meta.get_docfield(doctype, fieldname, name).formatter = formatter;
	},

	set_indicator_formatter: function (doctype, fieldname, name, get_text, get_color) {
		saashq.meta.get_docfield(doctype, fieldname, name).formatter = function (
			value,
			df,
			options,
			doc
		) {
			return repl('<span class="indicator %(color)s">%(name)s</span>', {
				color: get_color(),
				name: get_text(),
			});
		};
	},

	get_docfields: function (doctype, name, filters) {
		var docfield_map = saashq.meta.get_docfield_copy(doctype, name);

		var docfields = saashq.meta.sort_docfields(docfield_map);

		if (filters) {
			docfields = saashq.utils.filter_dict(docfields, filters);
		}

		return docfields;
	},

	get_linked_fields: function (doctype) {
		return $.map(saashq.get_meta(doctype).fields, function (d) {
			return d.fieldtype == "Link" ? d.options : null;
		});
	},

	get_fields_to_check_permissions: function (doctype) {
		var fields = $.map(saashq.meta.get_docfields(doctype, name), function (df) {
			return df.fieldtype === "Link" && df.ignore_user_permissions !== 1 ? df : null;
		});
		fields = fields.concat({ label: "ID", fieldname: name, options: doctype });
		return fields;
	},

	sort_docfields: function (docs) {
		return $.map(docs, function (d) {
			return d;
		}).sort(function (a, b) {
			return a.idx - b.idx;
		});
	},

	get_docfield_copy: function (doctype, name) {
		if (!name) return saashq.meta.docfield_map[doctype];

		if (!(saashq.meta.docfield_copy[doctype] && saashq.meta.docfield_copy[doctype][name])) {
			saashq.meta.make_docfield_copy_for(doctype, name);
		}

		return saashq.meta.docfield_copy[doctype][name];
	},

	get_fieldnames: function (doctype, name, filters) {
		return $.map(
			saashq.utils.filter_dict(saashq.meta.docfield_map[doctype], filters),
			function (df) {
				return df.fieldname;
			}
		);
	},

	has_field: function (dt, fn) {
		let docfield_map = saashq.meta.docfield_map[dt];
		return docfield_map && docfield_map[fn];
	},

	get_table_fields: function (dt) {
		return $.map(saashq.meta.docfield_list[dt], function (d) {
			return saashq.model.table_fields.includes(d.fieldtype) ? d : null;
		});
	},

	get_doctype_for_field: function (doctype, key) {
		var out = null;
		if (saashq.model.std_fields_list.includes(key)) {
			// standard
			out = doctype;
		} else if (saashq.meta.has_field(doctype, key)) {
			// found in parent
			out = doctype;
		} else {
			saashq.meta.get_table_fields(doctype).every(function (d) {
				if (
					saashq.meta.has_field(d.options, key) ||
					saashq.model.child_table_field_list.includes(key)
				) {
					out = d.options;
					return false;
				}
				return true;
			});

			if (!out) {
				console.log(
					__("Warning: Unable to find {0} in any table related to {1}", [
						key,
						__(doctype),
					])
				);
			}
		}
		return out;
	},

	get_parentfield: function (parent_dt, child_dt) {
		var df = (saashq.get_meta(parent_dt).fields || []).filter(
			(df) => saashq.model.table_fields.includes(df.fieldtype) && df.options === child_dt
		);
		if (!df.length) throw "parentfield not found for " + parent_dt + ", " + child_dt;
		return df[0].fieldname;
	},

	get_label: function (dt, fn, dn) {
		var standard = {
			name: __("ID"),
			creation: __("Created On"),
			docstatus: __("Document Status"),
			idx: __("Index"),
			modified: __("Last Updated On"),
			modified_by: __("Last Updated By"),
			owner: __("Created By"),
			_user_tags: __("Tags"),
			_liked_by: __("Liked By"),
			_comments: __("Comments"),
			_assign: __("Assigned To"),
		};
		if (standard[fn]) {
			return standard[fn];
		} else {
			var df = this.get_docfield(dt, fn, dn);
			return (df ? df.label : "") || fn;
		}
	},

	get_print_sizes: function () {
		return [
			"A0",
			"A1",
			"A2",
			"A3",
			"A4",
			"A5",
			"A6",
			"A7",
			"A8",
			"A9",
			"B0",
			"B1",
			"B2",
			"B3",
			"B4",
			"B5",
			"B6",
			"B7",
			"B8",
			"B9",
			"B10",
			"C5E",
			"Comm10E",
			"DLE",
			"Executive",
			"Folio",
			"Ledger",
			"Legal",
			"Letter",
			"Tabloid",
			"Custom",
		];
	},

	get_print_formats: function (doctype) {
		var print_format_list = ["Standard"];
		var default_print_format = locals.DocType[doctype].default_print_format;
		let enable_raw_printing = saashq.model.get_doc(
			":Print Settings",
			"Print Settings"
		).enable_raw_printing;
		var print_formats = saashq
			.get_list("Print Format", { doc_type: doctype })
			.sort(function (a, b) {
				return a > b ? 1 : -1;
			});
		$.each(print_formats, function (i, d) {
			if (
				!print_format_list.includes(d.name) &&
				d.print_format_type !== "JS" &&
				(cint(enable_raw_printing) || !d.raw_printing)
			) {
				print_format_list.push(d.name);
			}
		});

		if (default_print_format && default_print_format != "Standard") {
			var index = print_format_list.indexOf(default_print_format);
			print_format_list.splice(index, 1).sort();
			print_format_list.unshift(default_print_format);
		}

		return print_format_list;
	},

	get_field_currency: function (df, doc) {
		var currency = saashq.boot.sysdefaults.currency;
		if (!doc && cur_frm) doc = cur_frm.doc;

		if (df && df.options) {
			if (df.options.indexOf(":") != -1) {
				var options = df.options.split(":");
				if (options.length == 3) {
					let docname = null;
					if (doc) {
						// get reference record e.g. Company
						docname = doc[options[1]];
						if (!docname && cur_frm) {
							docname = cur_frm.doc[options[1]];
						}
					} else {
						// Try to get default value, useful for cases like Company overridden in session defaults
						docname = saashq.defaults.get_user_default(options[1]);
					}
					currency =
						saashq.model.get_value(options[0], docname, options[2]) ||
						saashq.model.get_value(":" + options[0], docname, options[2]) ||
						currency;
				}
			} else if (doc && doc[df.options]) {
				currency = doc[df.options];
			} else if (cur_frm && cur_frm.doc[df.options]) {
				currency = cur_frm.doc[df.options];
			}
		}
		return currency;
	},

	get_field_precision: function (df, doc) {
		var precision = null;
		if (df && df.precision) {
			precision = cint(df.precision);
		} else if (df && df.fieldtype === "Currency") {
			precision = cint(saashq.defaults.get_default("currency_precision"));
			if (!precision) {
				var number_format = get_number_format();
				var number_format_info = get_number_format_info(number_format);
				precision = number_format_info.precision;
			}
		} else {
			precision = cint(saashq.defaults.get_default("float_precision")) || 3;
		}
		return precision;
	},
});
