// Copyright (c) 2019, Saashq Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

saashq.provide("saashq.energy_points");

Object.assign(saashq.energy_points, {
	get_points(points) {
		return `<span class="bold" style="color: ${points >= 0 ? "#45A163" : "#e42121"}">
			${points > 0 ? "+" : ""}${points}
		</span>`;
	},
	format_form_log(log) {
		const separator = `<span>&nbsp;-&nbsp;</span>`;
		return `<span>
  			<!--${this.get_points(log.points)}&nbsp;-->
  			<a href="/app/energy-point-log/${log.name}">${this.get_form_log_message(log)}</a>
  			${log.reason ? separator + log.reason : ""}
  		</span>`;
	},
	format_history_log(log) {
		// redundant code to honor readability and to avoid confusion
		const separator = `<span>&nbsp;-&nbsp;</span>`;
		const route = saashq.utils.get_form_link(log.reference_doctype, log.reference_name);
		return `<div class="flex">
  			<span class="${log.points >= 0 ? "green" : "red"} mr-2">
  				${this.get_points(log.points)}
  			</span>
  			<a href="${route}" class="text-muted">${this.get_history_log_message(log)}</a>
  			${log.reason ? separator + log.reason : ""}
  			${separator + saashq.datetime.comment_when(log.creation)}
  		</div>`;
	},
	get_history_log_message(log) {
		const owner_name = saashq.user.full_name(log.owner).bold();
		const ref_doc = log.reference_name;

		if (log.type === "Appreciation") {
			return __("{0} appreciated on {1}", [owner_name, ref_doc]);
		}
		if (log.type === "Criticism") {
			return __("{0} criticized on {1}", [owner_name, ref_doc]);
		}
		if (log.type === "Revert") {
			return __("{0} reverted {1}", [owner_name, log.revert_of]);
		}
		return __("via automatic rule {0} on {1}", [log.rule.bold(), ref_doc]);
	},
	get_form_log_message(log) {
		// redundant code to honor readability and to avoid confusion
		const owner_name = saashq.user.full_name(log.owner).bold();
		const user = saashq.user.full_name(log.user).bold();
		if (log.type === "Appreciation") {
			return __("{0} appreciated {1}", [owner_name, user]);
		}
		if (log.type === "Criticism") {
			return __("{0} criticized {1}", [owner_name, user]);
		}
		if (log.type === "Revert") {
			return __("{0} reverted {1}", [owner_name, log.revert_of]);
		}
		return __("gained by {0} via automatic rule {1}", [user, log.rule.bold()]);
	},
});
