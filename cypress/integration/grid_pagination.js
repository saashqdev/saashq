context("Grid Pagination", () => {
	beforeEach(() => {
		cy.login();
		cy.visit("/app/website");
	});
	before(() => {
		cy.login();
		cy.visit("/app/website");
		return cy
			.window()
			.its("saashq")
			.then((saashq) => {
				return saashq.call(
					"saashq.tests.ui_test_helpers.create_contact_phone_nos_records"
				);
			});
	});
	it("creates pages for child table", () => {
		cy.visit("/app/contact/Test Contact");
		cy.get('.saashq-control[data-fieldname="phone_nos"]').as("table");
		cy.get("@table").find(".current-page-number").should("have.value", "1");
		cy.get("@table").find(".total-page-number").should("contain", "20");
		cy.get("@table").find(".grid-body .grid-row").should("have.length", 50);
	});
	it("goes to the next and previous page", () => {
		cy.visit("/app/contact/Test Contact");
		cy.get('.saashq-control[data-fieldname="phone_nos"]').as("table");
		cy.get("@table").find(".next-page").click();
		cy.get("@table").find(".current-page-number").should("have.value", "2");
		cy.get("@table")
			.find(".grid-body .grid-row")
			.first()
			.should("have.attr", "data-idx", "51");
		cy.get("@table").find(".prev-page").click();
		cy.get("@table").find(".current-page-number").should("have.value", "1");
		cy.get("@table").find(".grid-body .grid-row").first().should("have.attr", "data-idx", "1");
	});
	it("adds and deletes rows and changes page", () => {
		cy.visit("/app/contact/Test Contact");
		cy.get('.saashq-control[data-fieldname="phone_nos"]').as("table");
		cy.get("@table").findByRole("button", { name: "Add Row" }).click();
		cy.get("@table").find(".grid-body .row-index").should("contain", 1001);
		cy.get("@table").find(".current-page-number").should("have.value", "21");
		cy.get("@table").find(".total-page-number").should("contain", "21");
		cy.get("@table").find(".grid-body .grid-row .grid-row-check").click({ force: true });
		cy.get("@table").findByRole("button", { name: "Delete" }).click();
		cy.get("@table").find(".grid-body .row-index").last().should("contain", 1000);
		cy.get("@table").find(".current-page-number").should("have.value", "20");
		cy.get("@table").find(".total-page-number").should("contain", "20");
	});
	it("go to specific page, use up and down arrow, type characters, 0 page and more than existing page", () => {
		cy.visit("/app/contact/Test Contact");
		cy.get('.saashq-control[data-fieldname="phone_nos"]').as("table");
		cy.get("@table").find(".current-page-number").focus().clear().type("17").blur();
		cy.get("@table").find(".grid-body .row-index").should("contain", 801);

		cy.get("@table").find(".current-page-number").focus().type("{uparrow}{uparrow}");
		cy.get("@table").find(".current-page-number").should("have.value", "19");

		cy.get("@table").find(".current-page-number").focus().type("{downarrow}{downarrow}");
		cy.get("@table").find(".current-page-number").should("have.value", "17");

		cy.get("@table").find(".current-page-number").focus().clear().type("700").blur();
		cy.get("@table").find(".current-page-number").should("have.value", "20");

		cy.get("@table").find(".current-page-number").focus().clear().type("0").blur();
		cy.get("@table").find(".current-page-number").should("have.value", "1");

		cy.get("@table").find(".current-page-number").focus().clear().type("abc").blur();
		cy.get("@table").find(".current-page-number").should("have.value", "1");
	});
	// it('deletes all rows', ()=> {
	// 	cy.visit('/app/contact/Test Contact');
	// 	cy.get('.saashq-control[data-fieldname="phone_nos"]').as('table');
	// 	cy.get('@table').find('.grid-heading-row .grid-row-check').click({force: true});
	// 	cy.get('@table').find('button.grid-remove-all-rows').click();
	// 	cy.get('.modal-dialog .btn-primary').contains('Yes').click();
	// 	cy.get('@table').find('.grid-body .grid-row').should('have.length', 0);
	// });
});
