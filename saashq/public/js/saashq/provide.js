// Copyright (c) 2015, Saashq Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// provide a namespace
if (!window.saashq) window.saashq = {};

saashq.provide = function (namespace) {
	// docs: create a namespace //
	var nsl = namespace.split(".");
	var parent = window;
	for (var i = 0; i < nsl.length; i++) {
		var n = nsl[i];
		if (!parent[n]) {
			parent[n] = {};
		}
		parent = parent[n];
	}
	return parent;
};

saashq.provide("locals");
saashq.provide("saashq.flags");
saashq.provide("saashq.settings");
saashq.provide("saashq.utils");
saashq.provide("saashq.ui.form");
saashq.provide("saashq.modules");
saashq.provide("saashq.templates");
saashq.provide("saashq.test_data");
saashq.provide("saashq.utils");
saashq.provide("saashq.model");
saashq.provide("saashq.user");
saashq.provide("saashq.session");
saashq.provide("saashq._messages");
saashq.provide("locals.DocType");

// for listviews
saashq.provide("saashq.listview_settings");
saashq.provide("saashq.tour");
saashq.provide("saashq.listview_parent_route");

// constants
window.NEWLINE = "\n";
window.TAB = 9;
window.UP_ARROW = 38;
window.DOWN_ARROW = 40;

// proxy for user globals defined in desk.js

// API globals
window.cur_frm = null;
