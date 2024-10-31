// Copyright (c) 2015, Saashq Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// for translation
saashq._ = function (txt, replace, context = null) {
	if (!txt) return txt;
	if (typeof txt != "string") return txt;

	let translated_text = "";

	let key = txt; // txt.replace(/\n/g, "");
	if (context) {
		translated_text = saashq._messages[`${key}:${context}`];
	}

	if (!translated_text) {
		translated_text = saashq._messages[key] || txt;
	}

	if (replace && typeof replace === "object") {
		translated_text = $.format(translated_text, replace);
	}
	return translated_text;
};

window.__ = saashq._;

saashq.get_languages = function () {
	if (!saashq.languages) {
		saashq.languages = [];
		$.each(saashq.boot.lang_dict, function (lang, value) {
			saashq.languages.push({ label: lang, value: value });
		});
		saashq.languages = saashq.languages.sort(function (a, b) {
			return a.value < b.value ? -1 : 1;
		});
	}
	return saashq.languages;
};
