// Copyright (c) 2023-Present, SaasHQ
// MIT License. See license.txt

saashq.provide("saashq.model");

$.extend(saashq.model, {
	all_fieldtypes: [
		"Autocomplete",
		"Attach",
		"Attach Image",
		"Barcode",
		"Button",
		"Check",
		"Code",
		"Color",
		"Currency",
		"Data",
		"Date",
		"Datetime",
		"Duration",
		"Dynamic Link",
		"Float",
		"Geolocation",
		"Heading",
		"HTML",
		"HTML Editor",
		"Icon",
		"Image",
		"Int",
		"JSON",
		"Link",
		"Long Text",
		"Markdown Editor",
		"Password",
		"Percent",
		"Phone",
		"Read Only",
		"Rating",
		"Select",
		"Signature",
		"Small Text",
		"Table",
		"Table MultiSelect",
		"Text",
		"Text Editor",
		"Time",
	],

	no_value_type: [
		"Section Break",
		"Column Break",
		"Tab Break",
		"HTML",
		"Table",
		"Table MultiSelect",
		"Button",
		"Image",
		"Fold",
		"Heading",
	],

	layout_fields: ["Section Break", "Column Break", "Tab Break", "Fold"],

	std_fields_list: [
		"name",
		"owner",
		"creation",
		"modified",
		"modified_by",
		"_user_tags",
		"_comments",
		"_assign",
		"_liked_by",
		"docstatus",
		"idx",
	],

	child_table_field_list: ["parent", "parenttype", "parentfield"],

	core_doctypes_list: [
		"DocType",
		"DocField",
		"DocPerm",
		"User",
		"Role",
		"Has Role",
		"Page",
		"Module Def",
		"Print Format",
		"Report",
		"Customize Form",
		"Customize Form Field",
		"Property Setter",
		"Custom Field",
		"Client Script",
	],

	restricted_fields: [
		"name",
		"parent",
		"creation",
		"modified",
		"modified_by",
		"parentfield",
		"parenttype",
		"file_list",
		"flags",
		"docstatus",
	],

	html_fieldtypes: [
		"Text Editor",
		"Text",
		"Small Text",
		"Long Text",
		"HTML Editor",
		"Markdown Editor",
		"Code",
	],

	std_fields: [
		{ fieldname: "name", fieldtype: "Link", label: __("ID") },
		{ fieldname: "owner", fieldtype: "Link", label: __("Created By"), options: "User" },
		{ fieldname: "idx", fieldtype: "Int", label: __("Index") },
		{ fieldname: "creation", fieldtype: "Datetime", label: __("Created On") },
		{ fieldname: "modified", fieldtype: "Datetime", label: __("Last Updated On") },
		{
			fieldname: "modified_by",
			fieldtype: "Link",
			label: __("Last Updated By"),
			options: "User",
		},
		{ fieldname: "_user_tags", fieldtype: "Data", label: __("Tags") },
		{ fieldname: "_liked_by", fieldtype: "Data", label: __("Liked By") },
		{ fieldname: "_comments", fieldtype: "Text", label: __("Comments") },
		{ fieldname: "_assign", fieldtype: "Text", label: __("Assigned To") },
		{ fieldname: "docstatus", fieldtype: "Int", label: __("Document Status") },
	],

	numeric_fieldtypes: ["Int", "Float", "Currency", "Percent", "Duration"],

	std_fields_table: [{ fieldname: "parent", fieldtype: "Data", label: __("Parent") }],

	table_fields: ["Table", "Table MultiSelect"],

	new_names: {},
	events: {},
	user_settings: {},

	init: function () {
		// setup refresh if the document is updated somewhere else
		saashq.realtime.on("doc_update", function (data) {
			var doc = locals[data.doctype] && locals[data.doctype][data.name];

			if (doc) {
				// current document is dirty, show message if its not me
				if (
					saashq.get_route()[0] === "Form" &&
					cur_frm.doc.doctype === doc.doctype &&
					cur_frm.doc.name === doc.name
				) {
					if (data.modified !== cur_frm.doc.modified && !saashq.ui.form.is_saving) {
						if (!cur_frm.is_dirty()) {
							cur_frm.debounced_reload_doc();
						} else {
							doc.__needs_refresh = true;
							cur_frm.show_conflict_message();
						}
					}
				} else {
					if (!doc.__unsaved) {
						// no local changes, remove from locals
						saashq.model.remove_from_locals(doc.doctype, doc.name);
					} else {
						// show message when user navigates back
						doc.__needs_refresh = true;
					}
				}
			}
		});
	},

	is_value_type: function (fieldtype) {
		if (typeof fieldtype == "object") {
			fieldtype = fieldtype.fieldtype;
		}
		// not in no-value type
		return saashq.model.no_value_type.indexOf(fieldtype) === -1;
	},

	is_non_std_field: function (fieldname) {
		return ![...saashq.model.std_fields_list, ...saashq.model.child_table_field_list].includes(
			fieldname
		);
	},

	get_std_field: function (fieldname, ignore = false) {
		var docfield = $.map(
			[].concat(saashq.model.std_fields).concat(saashq.model.std_fields_table),
			function (d) {
				if (d.fieldname == fieldname) return d;
			}
		);
		if (!docfield.length) {
			//Standard fields are ignored in case of adding columns as a result of groupby
			if (ignore) {
				return { fieldname: fieldname };
			} else {
				saashq.msgprint(__("Unknown Column: {0}", [fieldname]));
			}
		}
		return docfield[0];
	},

	get_from_localstorage: function (doctype) {
		if (localStorage["_doctype:" + doctype]) {
			return JSON.parse(localStorage["_doctype:" + doctype]);
		}
	},

	set_in_localstorage: function (doctype, docs) {
		try {
			localStorage["_doctype:" + doctype] = JSON.stringify(docs);
		} catch (e) {
			// if quota is exceeded, clear local storage and set item
			console.warn("localStorage quota exceeded, clearing doctype cache");
			saashq.model.clear_local_storage();
			localStorage["_doctype:" + doctype] = JSON.stringify(docs);
		}
	},

	clear_local_storage: function () {
		for (var key in localStorage) {
			if (key.startsWith("_doctype:")) {
				localStorage.removeItem(key);
			}
		}
	},

	with_doctype: function (doctype, callback, async) {
		if (locals.DocType[doctype]) {
			callback && callback();
			return Promise.resolve();
		} else {
			let cached_timestamp = null;
			let meta = null;

			let cached_docs = saashq.model.get_from_localstorage(doctype);

			if (cached_docs) {
				meta = cached_docs.filter((doc) => doc.name === doctype)[0];
				if (meta) {
					cached_timestamp = meta.modified;
				}
			}

			return saashq.call({
				method: "saashq.desk.form.load.getdoctype",
				type: "GET",
				args: {
					doctype: doctype,
					with_parent: 1,
					cached_timestamp: cached_timestamp,
				},
				async: async,
				callback: function (r) {
					if (r.exc) {
						saashq.msgprint(__("Unable to load: {0}", [__(doctype)]));
						throw "No doctype";
					}
					if (r.message == "use_cache") {
						saashq.model.sync(meta);
					} else {
						saashq.model.set_in_localstorage(doctype, r.docs);
						meta = r.docs[0];
					}
					saashq.model.init_doctype(meta);

					if (r.user_settings) {
						// remember filters and other settings from last view
						saashq.model.user_settings[doctype] = JSON.parse(r.user_settings);
						saashq.model.user_settings[doctype].updated_on = moment().toString();
					}
					callback && callback(r);
				},
			});
		}
	},

	init_doctype: function (meta) {
		if (meta.name === "DocType") {
			// store doctype "meta" separate as it will be overridden by doctype "doc"
			// meta has sugar, like __js and other properties that doc won't have
			saashq.meta.__doctype_meta = JSON.parse(JSON.stringify(meta));
		}
		for (const asset_key of [
			"__list_js",
			"__custom_list_js",
			"__calendar_js",
			"__map_js",
			"__tree_js",
		]) {
			if (meta[asset_key]) {
				new Function(meta[asset_key])();
			}
		}

		if (meta.__templates) {
			$.extend(saashq.templates, meta.__templates);
		}
	},

	with_doc: function (doctype, name, callback) {
		return new Promise((resolve) => {
			if (!name) name = doctype; // single type
			if (
				locals[doctype] &&
				locals[doctype][name] &&
				saashq.model.get_docinfo(doctype, name)
			) {
				callback && callback(name);
				resolve(saashq.get_doc(doctype, name));
			} else {
				return saashq.call({
					method: "saashq.desk.form.load.getdoc",
					type: "GET",
					args: {
						doctype: doctype,
						name: name,
					},
					callback: function (r) {
						callback && callback(name, r);
						resolve(saashq.get_doc(doctype, name));
					},
				});
			}
		});
	},

	get_docinfo: function (doctype, name) {
		return (saashq.model.docinfo[doctype] && saashq.model.docinfo[doctype][name]) || null;
	},

	set_docinfo: function (doctype, name, key, value) {
		if (saashq.model.docinfo[doctype] && saashq.model.docinfo[doctype][name]) {
			saashq.model.docinfo[doctype][name][key] = value;
		}
	},

	get_shared: function (doctype, name) {
		return saashq.model.get_docinfo(doctype, name).shared;
	},

	get_server_module_name: function (doctype) {
		var dt = saashq.model.scrub(doctype);
		var module = saashq.model.scrub(locals.DocType[doctype].module);
		var app = saashq.boot.module_app[module];
		return app + "." + module + ".doctype." + dt + "." + dt;
	},

	scrub: function (txt) {
		return txt.replace(/ /g, "_").toLowerCase(); // use to slugify or create a slug, a "code-friendly" string
	},

	unscrub: function (txt) {
		return (txt || "").replace(/-|_/g, " ").replace(/\w*/g, function (keywords) {
			return keywords.charAt(0).toUpperCase() + keywords.substr(1).toLowerCase();
		});
	},

	can_create: function (doctype) {
		return saashq.boot.user.can_create.indexOf(doctype) !== -1;
	},

	can_select: function (doctype) {
		if (saashq.boot.user) {
			return saashq.boot.user.can_select.indexOf(doctype) !== -1;
		}
	},

	can_read: function (doctype) {
		if (saashq.boot.user) {
			return saashq.boot.user.can_read.indexOf(doctype) !== -1;
		}
	},

	can_write: function (doctype) {
		return saashq.boot.user.can_write.indexOf(doctype) !== -1;
	},

	can_get_report: function (doctype) {
		return saashq.boot.user.can_get_report.indexOf(doctype) !== -1;
	},

	can_delete: function (doctype) {
		if (!doctype) return false;
		return saashq.boot.user.can_delete.indexOf(doctype) !== -1;
	},

	can_submit: function (doctype) {
		if (!doctype) return false;
		return saashq.boot.user.can_submit.indexOf(doctype) !== -1;
	},

	can_cancel: function (doctype) {
		if (!doctype) return false;
		return saashq.boot.user.can_cancel.indexOf(doctype) !== -1;
	},

	has_workflow: function (doctype) {
		return saashq.get_list("Workflow", { document_type: doctype, is_active: 1 }).length;
	},

	is_submittable: function (doctype) {
		if (!doctype) return false;
		return locals.DocType[doctype] && locals.DocType[doctype].is_submittable;
	},

	is_table: function (doctype) {
		if (!doctype) return false;
		return locals.DocType[doctype] && locals.DocType[doctype].istable;
	},

	is_single: function (doctype) {
		if (!doctype) return false;
		return saashq.boot.single_types.indexOf(doctype) != -1;
	},

	is_tree: function (doctype) {
		if (!doctype) return false;
		return locals.DocType[doctype] && locals.DocType[doctype].is_tree;
	},

	is_fresh(doc) {
		// returns true if document has been recently loaded (5 seconds ago)
		return doc && doc.__last_sync_on && new Date() - doc.__last_sync_on < 5000;
	},

	can_import: function (doctype, frm, meta = null) {
		if (meta && !meta.allow_import) return false;

		// system manager can always import
		if (saashq.user_roles.includes("System Manager")) return true;

		if (frm) return frm.perm[0].import === 1;
		return saashq.boot.user.can_import.indexOf(doctype) !== -1;
	},

	can_export: function (doctype, frm) {
		// system manager can always export
		if (saashq.user_roles.includes("System Manager")) return true;

		if (frm) return frm.perm[0].export === 1;
		return saashq.boot.user.can_export.indexOf(doctype) !== -1;
	},

	can_print: function (doctype, frm) {
		if (frm) return frm.perm[0].print === 1;
		return saashq.boot.user.can_print.indexOf(doctype) !== -1;
	},

	can_email: function (doctype, frm) {
		if (frm) return frm.perm[0].email === 1;
		return saashq.boot.user.can_email.indexOf(doctype) !== -1;
	},

	can_share: function (doctype, frm) {
		let disable_sharing = cint(saashq.sys_defaults.disable_document_sharing);

		if (disable_sharing && saashq.session.user !== "Administrator") {
			return false;
		}

		if (frm) {
			return frm.perm[0].share === 1;
		}
		return saashq.boot.user.can_share.indexOf(doctype) !== -1;
	},

	has_value: function (dt, dn, fn) {
		// return true if property has value
		var val = locals[dt] && locals[dt][dn] && locals[dt][dn][fn];
		var df = saashq.meta.get_docfield(dt, fn, dn);

		let ret;
		if (saashq.model.table_fields.includes(df.fieldtype)) {
			ret = false;
			$.each(locals[df.options] || {}, function (k, d) {
				if (d.parent == dn && d.parenttype == dt && d.parentfield == df.fieldname) {
					ret = true;
					return false;
				}
			});
		} else {
			ret = !is_null(val);
		}
		return ret ? true : false;
	},

	get_list: function (doctype, filters) {
		var docsdict = locals[doctype] || locals[":" + doctype] || {};
		if ($.isEmptyObject(docsdict)) return [];
		return saashq.utils.filter_dict(docsdict, filters);
	},

	get_value: function (doctype, filters, fieldname, callback) {
		if (callback) {
			saashq.call({
				method: "saashq.client.get_value",
				args: {
					doctype: doctype,
					fieldname: fieldname,
					filters: filters,
				},
				callback: function (r) {
					if (!r.exc) {
						callback(r.message);
					}
				},
			});
		} else {
			if (
				["number", "string"].includes(typeof filters) &&
				locals[doctype] &&
				locals[doctype][filters]
			) {
				return locals[doctype][filters][fieldname];
			} else {
				var l = saashq.get_list(doctype, filters);
				return l.length && l[0] ? l[0][fieldname] : null;
			}
		}
	},

	set_value: function (
		doctype,
		docname,
		fieldname,
		value,
		fieldtype,
		skip_dirty_trigger = false
	) {
		/* help: Set a value locally (if changed) and execute triggers */

		var doc;
		if ($.isPlainObject(doctype)) {
			// first parameter is the doc, shift parameters to the left
			doc = doctype;
			fieldname = docname;
			value = fieldname;
		} else {
			doc = locals[doctype] && locals[doctype][docname];
		}

		let to_update = fieldname;
		let tasks = [];
		if (!$.isPlainObject(to_update)) {
			to_update = {};
			to_update[fieldname] = value;
		}

		$.each(to_update, (key, value) => {
			if (doc && doc[key] !== value) {
				if (doc.__unedited && !(!doc[key] && !value)) {
					// unset unedited flag for virgin rows
					doc.__unedited = false;
				}

				doc[key] = value;
				tasks.push(() => saashq.model.trigger(key, value, doc, skip_dirty_trigger));
			} else {
				// execute link triggers (want to reselect to execute triggers)
				if (["Link", "Dynamic Link"].includes(fieldtype) && doc) {
					tasks.push(() => saashq.model.trigger(key, value, doc, skip_dirty_trigger));
				}
			}
		});

		return saashq.run_serially(tasks);
	},

	on: function (doctype, fieldname, fn) {
		/* help: Attach a trigger on change of a particular field.
		To trigger on any change in a particular doctype, use fieldname as "*"
		*/
		/* example: saashq.model.on("Customer", "age", function(fieldname, value, doc) {
		  if(doc.age < 16) {
		   	saashq.msgprint("Warning, Customer must atleast be 16 years old.");
		    raise "CustomerAgeError";
		  }
		}) */
		saashq.provide("saashq.model.events." + doctype);
		if (!saashq.model.events[doctype][fieldname]) {
			saashq.model.events[doctype][fieldname] = [];
		}
		saashq.model.events[doctype][fieldname].push(fn);
	},

	trigger: function (fieldname, value, doc, skip_dirty_trigger = false) {
		const tasks = [];

		function enqueue_events(events) {
			if (!events) return;

			for (const fn of events) {
				if (!fn) continue;

				tasks.push(() => {
					const return_value = fn(fieldname, value, doc, skip_dirty_trigger);

					// if the trigger returns a promise, return it,
					// or use the default promise saashq.after_ajax
					if (return_value && return_value.then) {
						return return_value;
					} else {
						return saashq.after_server_call();
					}
				});
			}
		}

		if (saashq.model.events[doc.doctype]) {
			enqueue_events(saashq.model.events[doc.doctype][fieldname]);
			enqueue_events(saashq.model.events[doc.doctype]["*"]);
		}

		return saashq.run_serially(tasks);
	},

	get_doc: function (doctype, name) {
		if (!name) name = doctype;
		if ($.isPlainObject(name)) {
			var doc = saashq.get_list(doctype, name);
			return doc && doc.length ? doc[0] : null;
		}
		return locals[doctype] ? locals[doctype][name] : null;
	},

	get_children: function (doctype, parent, parentfield, filters) {
		let doc;
		if ($.isPlainObject(doctype)) {
			doc = doctype;
			filters = parentfield;
			parentfield = parent;
		} else {
			doc = saashq.get_doc(doctype, parent);
		}

		var children = doc[parentfield] || [];
		if (filters) {
			return saashq.utils.filter_dict(children, filters);
		} else {
			return children;
		}
	},

	clear_table: function (doc, parentfield) {
		for (const d of doc[parentfield] || []) {
			delete locals[d.doctype][d.name];
		}
		doc[parentfield] = [];
	},

	remove_from_locals: function (doctype, name) {
		this.clear_doc(doctype, name);
		if (saashq.views.formview[doctype]) {
			delete saashq.views.formview[doctype].frm.opendocs[name];
		}
	},

	clear_doc: function (doctype, name) {
		var doc = locals[doctype] && locals[doctype][name];
		if (!doc) return;

		var parent = null;
		if (doc.parenttype) {
			parent = doc.parent;
			var parenttype = doc.parenttype,
				parentfield = doc.parentfield;
		}
		delete locals[doctype][name];
		if (parent) {
			var parent_doc = locals[parenttype][parent];
			var newlist = [],
				idx = 1;
			$.each(parent_doc[parentfield], function (i, d) {
				if (d.name != name) {
					newlist.push(d);
					d.idx = idx;
					idx++;
				}
				parent_doc[parentfield] = newlist;
			});
		}
	},

	get_no_copy_list: function (doctype) {
		var no_copy_list = ["name", "amended_from", "amendment_date", "cancel_reason"];

		var docfields = saashq.get_meta(doctype).fields || [];
		for (var i = 0, j = docfields.length; i < j; i++) {
			var df = docfields[i];
			if (cint(df.no_copy)) no_copy_list.push(df.fieldname);
		}

		return no_copy_list;
	},

	delete_doc: function (doctype, docname, callback) {
		let title = docname;
		const title_field = saashq.get_meta(doctype).title_field;
		if (saashq.get_meta(doctype).autoname == "hash" && title_field) {
			const value = saashq.model.get_value(doctype, docname, title_field);
			if (value) {
				title = `${value} (${docname})`;
			}
		}
		saashq.confirm(__("Permanently delete {0}?", [title.bold()]), function () {
			return saashq.call({
				method: "saashq.client.delete",
				args: {
					doctype: doctype,
					name: docname,
				},
				freeze: true,
				freeze_message: __("Deleting {0}...", [title]),
				callback: function (r, rt) {
					if (!r.exc) {
						saashq.utils.play_sound("delete");
						saashq.model.clear_doc(doctype, docname);
						if (callback) callback(r, rt);
					}
				},
			});
		});
	},

	rename_doc: function (doctype, docname, callback) {
		let message = __("Merge with existing");
		let warning = __("This cannot be undone");
		let merge_label = message + " <b>(" + warning + ")</b>";

		var d = new saashq.ui.Dialog({
			title: __("Rename {0}", [__(docname)]),
			fields: [
				{
					label: __("New Name"),
					fieldname: "new_name",
					fieldtype: "Data",
					reqd: 1,
					default: docname,
				},
				{ label: merge_label, fieldtype: "Check", fieldname: "merge" },
			],
		});

		d.set_primary_action(__("Rename"), function () {
			d.hide();
			var args = d.get_values();
			if (!args) return;
			return saashq.call({
				method: "saashq.rename_doc",
				freeze: true,
				freeze_message: "Updating related fields...",
				args: {
					doctype: doctype,
					old: docname,
					new: args.new_name,
					merge: args.merge,
				},
				btn: d.get_primary_btn(),
				callback: function (r, rt) {
					if (!r.exc) {
						$(document).trigger("rename", [
							doctype,
							docname,
							r.message || args.new_name,
						]);
						if (locals[doctype] && locals[doctype][docname])
							delete locals[doctype][docname];
						d.hide();
						if (callback) callback(r.message);
					}
				},
			});
		});
		d.show();
	},

	round_floats_in: function (doc, fieldnames) {
		if (!doc) {
			return;
		}
		if (!fieldnames) {
			fieldnames = saashq.meta.get_fieldnames(doc.doctype, doc.parent, {
				fieldtype: ["in", ["Currency", "Float"]],
			});
		}
		for (var i = 0, j = fieldnames.length; i < j; i++) {
			var fieldname = fieldnames[i];
			doc[fieldname] = flt(doc[fieldname], precision(fieldname, doc));
		}
	},

	validate_missing: function (doc, fieldname) {
		if (!doc[fieldname]) {
			saashq.throw(
				__("Please specify") +
					": " +
					__(saashq.meta.get_label(doc.doctype, fieldname, doc.parent || doc.name))
			);
		}
	},

	get_all_docs: function (doc) {
		var all = [doc];
		for (var key in doc) {
			if ($.isArray(doc[key]) && !key.startsWith("_")) {
				var children = doc[key];
				for (var i = 0, l = children.length; i < l; i++) {
					all.push(children[i]);
				}
			}
		}
		return all;
	},

	get_full_column_name: function (fieldname, doctype) {
		if (fieldname.includes("`tab")) return fieldname;
		return "`tab" + doctype + "`.`" + fieldname + "`";
	},

	is_numeric_field: function (fieldtype) {
		if (!fieldtype) return;
		if (typeof fieldtype === "object") {
			fieldtype = fieldtype.fieldtype;
		}
		return saashq.model.numeric_fieldtypes.includes(fieldtype);
	},

	set_default_views_for_doctype(doctype, frm) {
		saashq.model.with_doctype(doctype, () => {
			let meta = saashq.get_meta(doctype);
			let default_views = ["List", "Report", "Dashboard", "Kanban"];

			if (meta.is_calendar_and_gantt && saashq.views.calendar[doctype]) {
				let views = ["Calendar", "Gantt"];
				default_views.push(...views);
			}

			if (meta.is_tree) {
				default_views.push("Tree");
			}

			if (frm.doc.image_field) {
				default_views.push("Image");
			}

			if (doctype === "Communication" && saashq.boot.email_accounts.length) {
				default_views.push("Inbox");
			}

			if (
				(frm.doc.fields?.find((i) => i.fieldname === "latitude") &&
					frm.doc.fields?.find((i) => i.fieldname === "longitude")) ||
				frm.doc.fields?.find(
					(i) => i.fieldname === "location" && i.fieldtype == "Geolocation"
				)
			) {
				default_views.push("Map");
			}

			frm.set_df_property("default_view", "options", default_views);
		});
	},
});

// legacy
saashq.get_doc = saashq.model.get_doc;
saashq.get_children = saashq.model.get_children;
saashq.get_list = saashq.model.get_list;

var getchildren = function (doctype, parent, parentfield) {
	var children = [];
	$.each(locals[doctype] || {}, function (i, d) {
		if (d.parent === parent && d.parentfield === parentfield) {
			children.push(d);
		}
	});
	return children;
};
