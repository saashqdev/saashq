import data_field_validation_doctype from "../fixtures/data_field_validation_doctype";
const doctype_name = data_field_validation_doctype.name;

context("Data Field Input Validation in New Form", () => {
	before(() => {
		cy.login();
		cy.visit("/app/website");
		return cy.insert_doc("DocType", data_field_validation_doctype, true);
	});

	function validateField(fieldname, invalid_value, valid_value) {
		// Invalid, should have has-error class
		cy.get_field(fieldname).clear().type(invalid_value).blur();
		cy.get(`.saashq-control[data-fieldname="${fieldname}"]`).should("have.class", "has-error");
		// Valid value, should not have has-error class
		cy.get_field(fieldname).clear().type(valid_value);
		cy.get(`.saashq-control[data-fieldname="${fieldname}"]`).should(
			"not.have.class",
			"has-error"
		);
	}

	describe("Data Field Options", () => {
		it("should validate email address", () => {
			cy.new_form(doctype_name);
			validateField("email", "captian", "hello@test.com");
		});

		it("should validate URL", () => {
			validateField("url", "jkl", "https://saashq.org");
			validateField("url", "abcd.com", "http://google.com/home");
			validateField("url", "&&http://google.uae", "gopher://saashq.org");
			validateField("url", "ftt2:://google.in?q=news", "ftps2://saashq.org/__/#home");
			validateField("url", "ftt2://", "ntps://localhost"); // For intranet URLs
		});

		it("should validate phone number", () => {
			validateField("phone", "america", "89787878");
		});

		it("should validate name", () => {
			validateField("person_name", " 777Hello", "James Bond");
		});
	});
});
