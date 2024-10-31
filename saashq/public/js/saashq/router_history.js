saashq.route_history_queue = [];
const routes_to_skip = ["Form", "social", "setup-wizard", "recorder"];

const save_routes = saashq.utils.debounce(() => {
	if (saashq.session.user === "Guest") return;
	const routes = saashq.route_history_queue;
	if (!routes.length) return;

	saashq.route_history_queue = [];

	saashq
		.xcall("saashq.desk.doctype.route_history.route_history.deferred_insert", {
			routes: routes,
		})
		.catch(() => {
			saashq.route_history_queue.concat(routes);
		});
}, 10000);

saashq.router.on("change", () => {
	const route = saashq.get_route();
	if (is_route_useful(route)) {
		saashq.route_history_queue.push({
			creation: saashq.datetime.now_datetime(),
			route: saashq.get_route_str(),
		});

		save_routes();
	}
});

function is_route_useful(route) {
	if (!route[1]) {
		return false;
	} else if ((route[0] === "List" && !route[2]) || routes_to_skip.includes(route[0])) {
		return false;
	} else {
		return true;
	}
}
