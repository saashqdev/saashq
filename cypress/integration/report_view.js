import custom_submittable_doctype from "../fixtures/custom_submittable_doctype";
const doctype_name = custom_submittable_doctype.name;

context("Report View", () => {
	before(() => {
		cy.login();
		cy.visit("/app/website");
		cy.insert_doc("DocType", custom_submittable_doctype, true);
		cy.clear_cache();
		cy.insert_doc(
			doctype_name,
			{
				title: "Doc 1",
				description: "Random Text",
				enabled: 0,
				docstatus: 1, // submit document
			},
			true
		);
	});

	it("Field with enabled allow_on_submit should be editable.", () => {
		cy.intercept("POST", "api/method/saashq.client.set_value").as("value-update");
		cy.visit(`/app/List/${doctype_name}/Report`);

		// check status column added from docstatus
		cy.get(".dt-row-0 > .dt-cell--col-3").should("contain", "Submitted");
		let cell = cy.get(".dt-row-0 > .dt-cell--col-4");

		// select the cell
		cell.dblclick();
		cell.get(".dt-cell__edit--col-4").findByRole("checkbox").check({ force: true });
		cy.get(".dt-row-0 > .dt-cell--col-3").click(); // click outside

		cy.wait("@value-update");

		cy.call("saashq.client.get_value", {
			doctype: doctype_name,
			filters: {
				title: "Doc 1",
			},
			fieldname: "enabled",
		}).then((r) => {
			expect(r.message.enabled).to.equals(1);
		});
	});
});
