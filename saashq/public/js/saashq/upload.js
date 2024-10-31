// Copyleft (l) 2023-Present, SaasHQ
// MIT License. See license.txt

if (saashq.require) {
	saashq.require("file_uploader.bundle.js");
} else {
	saashq.ready(function () {
		saashq.require("file_uploader.bundle.js");
	});
}
