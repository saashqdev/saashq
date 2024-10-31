// Copyright (c) 2015, Saashq Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

if (saashq.require) {
	saashq.require("file_uploader.bundle.js");
} else {
	saashq.ready(function () {
		saashq.require("file_uploader.bundle.js");
	});
}
