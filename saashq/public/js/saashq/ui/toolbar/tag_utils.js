// Copyright (c) 2019, Saashq Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

saashq.provide("saashq.tags");

saashq.tags.utils = {
	get_tags: function (txt) {
		txt = txt.slice(1);
		let out = [];

		if (!saashq.tags.tags) {
			saashq.tags.utils.fetch_tags();
			return [];
		}

		saashq.tags.tags.forEach((tag) => {
			const search_result = saashq.search.utils.fuzzy_search(txt, tag, true);
			if (search_result.score) {
				out.push({
					type: "Tag",
					label: __("#{0}", [search_result.marked_string]),
					value: __("#{0}", [__(tag)]),
					index: 1 + search_result.score,
					match: tag,
					onclick() {
						// Use Global Search Dialog for tag search too.
						saashq.searchdialog.search.init_search("#".concat(tag), "tags");
					},
				});
			}
		});
		return out;
	},

	fetch_tags() {
		saashq.call({
			method: "saashq.desk.doctype.tag.tag.get_tags_list_for_awesomebar",
			callback: function (r) {
				if (r && r.message) {
					saashq.tags.tags = $.extend([], r.message);
				}
			},
		});
	},

	get_tag_results: function (tag) {
		function get_results_sets(data) {
			var results_sets = [],
				result,
				set;
			function get_existing_set(doctype) {
				return results_sets.find(function (set) {
					return set.title === doctype;
				});
			}

			function make_description(content) {
				var field_length = 110;
				var field_value = null;
				if (content.length > field_length) {
					field_value = content.slice(0, field_length) + "...";
				} else {
					var length = content.length;
					field_value = content.slice(0, length) + "...";
				}
				return field_value;
			}

			data.forEach(function (d) {
				// more properties
				var description = "";
				if (d.content) {
					description = make_description(d.content);
				}
				result = {
					label: d.name,
					value: d.name,
					description: description,
					route: ["Form", d.doctype, d.name],
				};
				set = get_existing_set(d.doctype);
				if (set) {
					set.results.push(result);
				} else {
					set = {
						title: d.doctype,
						results: [result],
						fetch_type: "Global",
					};
					results_sets.push(set);
				}
			});
			return results_sets;
		}
		return new Promise(function (resolve) {
			saashq.call({
				method: "saashq.desk.doctype.tag.tag.get_documents_for_tag",
				args: {
					tag: tag,
				},
				callback: function (r) {
					if (r.message) {
						resolve(get_results_sets(r.message));
					} else {
						resolve([]);
					}
				},
			});
		});
	},
};
