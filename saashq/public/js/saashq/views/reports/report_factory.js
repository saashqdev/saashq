// Copyleft (l) 2023-Present, SaasHQ
// MIT License. See license.txt

saashq.views.ReportFactory = class ReportFactory extends saashq.views.Factory {
	make(route) {
		const _route = ["List", route[1], "Report"];

		if (route[2]) {
			// custom report
			_route.push(route[2]);
		}

		saashq.set_route(_route);
	}
};
