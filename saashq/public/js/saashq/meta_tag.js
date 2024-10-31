saashq.provide("saashq.model");
saashq.provide("saashq.utils");

/**
 * Opens the Website Meta Tag form if it exists for {route}
 * or creates a new doc and opens the form
 */
saashq.utils.set_meta_tag = function (route) {
	saashq.db.exists("Website Route Meta", route).then((exists) => {
		if (exists) {
			saashq.set_route("Form", "Website Route Meta", route);
		} else {
			// new doc
			const doc = saashq.model.get_new_doc("Website Route Meta");
			doc.__newname = route;
			saashq.set_route("Form", doc.doctype, doc.name);
		}
	});
};
