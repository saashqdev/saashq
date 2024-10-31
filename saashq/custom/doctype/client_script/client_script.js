// Copyleft (l) 2023-Present, Saashq Technologies and contributors
// For license information, please see license.txt

saashq.ui.form.on("Client Script", {
	setup(frm) {
		frm.get_field("sample").html(SAMPLE_HTML);
	},
	refresh(frm) {
		if (frm.doc.dt && frm.doc.script) {
			frm.add_custom_button(__("Go to {0}", [frm.doc.dt]), () =>
				saashq.set_route("List", frm.doc.dt, "List")
			);
		}

		if (frm.doc.view == "Form") {
			frm.add_custom_button(__("Add script for Child Table"), () => {
				saashq.model.with_doctype(frm.doc.dt, () => {
					const child_tables = saashq.meta
						.get_docfields(frm.doc.dt, null, {
							fieldtype: "Table",
						})
						.map((df) => df.options);

					const d = new saashq.ui.Dialog({
						title: __("Select Child Table"),
						fields: [
							{
								label: __("Select Child Table"),
								fieldtype: "Link",
								fieldname: "cdt",
								options: "DocType",
								get_query: () => {
									return {
										filters: {
											istable: 1,
											name: ["in", child_tables],
										},
									};
								},
							},
						],
						primary_action: ({ cdt }) => {
							cdt = d.get_field("cdt").value;
							frm.events.add_script_for_doctype(frm, cdt);
							d.hide();
						},
					});

					d.show();
				});
			});

			if (!frm.is_new()) {
				frm.add_custom_button(__("Compare Versions"), () => {
					new saashq.ui.DiffView("Client Script", "script", frm.doc.name);
				});
			}
		}

		frm.set_query("dt", {
			filters: {
				istable: 0,
			},
		});
	},

	dt(frm) {
		frm.toggle_display("view", !saashq.boot.single_types.includes(frm.doc.dt));

		if (!frm.doc.script) {
			frm.events.add_script_for_doctype(frm, frm.doc.dt);
		}

		if (frm.doc.script && !frm.doc.script.includes(frm.doc.dt)) {
			frm.doc.script = "";
			frm.events.add_script_for_doctype(frm, frm.doc.dt);
		}
	},

	view(frm) {
		let has_form_boilerplate = frm.doc.script.includes("saashq.ui.form.on");
		if (frm.doc.view === "List" && has_form_boilerplate) {
			frm.set_value("script", "");
		}
		if (frm.doc.view === "Form" && !has_form_boilerplate) {
			frm.trigger("dt");
		}
	},

	add_script_for_doctype(frm, doctype) {
		if (!doctype) return;
		let boilerplate = `
saashq.ui.form.on('${doctype}', {
	refresh(frm) {
		// your code here
	}
})
		`.trim();
		let script = frm.doc.script || "";
		if (script) {
			script += "\n\n";
		}
		frm.set_value("script", script + boilerplate);
	},
});

const SAMPLE_HTML = `<h3>Client Script Help</h3>
<p>Client Scripts are executed only on the client-side (i.e. in Forms). Here are some examples to get you started</p>
<pre><code>

// fetch local_tax_no on selection of customer
// cur_frm.add_fetch(link_field,  source_fieldname,  target_fieldname);
cur_frm.add_fetch("customer",  "local_tax_no',  'local_tax_no');

// additional validation on dates
saashq.ui.form.on('Task',  'validate',  function(frm) {
    if (frm.doc.from_date &lt; get_today()) {
        msgprint('You can not select past date in From Date');
        validated = false;
    }
});

// make a field read-only after saving
saashq.ui.form.on('Task',  {
    refresh: function(frm) {
        // use the __islocal value of doc,  to check if the doc is saved or not
        frm.set_df_property('myfield',  'read_only',  frm.doc.__islocal ? 0 : 1);
    }
});

// additional permission check
saashq.ui.form.on('Task',  {
    validate: function(frm) {
        if(user=='user1@example.com' &amp;&amp; frm.doc.purpose!='Material Receipt') {
            msgprint('You are only allowed Material Receipt');
            validated = false;
        }
    }
});

// calculate sales incentive
saashq.ui.form.on('Sales Invoice',  {
    validate: function(frm) {
        // calculate incentives for each person on the deal
        total_incentive = 0
        $.each(frm.doc.sales_team,  function(i,  d) {
            // calculate incentive
            var incentive_percent = 2;
            if(frm.doc.base_grand_total &gt; 400) incentive_percent = 4;
            // actual incentive
            d.incentives = flt(frm.doc.base_grand_total) * incentive_percent / 100;
            total_incentive += flt(d.incentives)
        });
        frm.doc.total_incentive = total_incentive;
    }
})

</code></pre>`;
