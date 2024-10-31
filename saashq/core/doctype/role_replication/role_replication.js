// Copyright (c) 2024, Saashq Technologies and contributors
// For license information, please see license.txt

saashq.ui.form.on("Role Replication", {
	refresh(frm) {
		frm.disable_save();
		frm.page.set_primary_action(__("Replicate"), ($btn) => {
			$btn.text(__("Replicating..."));
			saashq.run_serially([
				() => saashq.dom.freeze("Replicating..."),
				() => frm.call("replicate_role"),
				() => saashq.dom.unfreeze(),
				() => saashq.msgprint(__("Replication completed.")),
				() => $btn.text(__("Replicate")),
			]);
		});
	},
});
