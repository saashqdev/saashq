context("Control Currency", () => {
	const fieldname = "currency_field";

	before(() => {
		cy.login();
		cy.visit("/app/website");
	});

	function get_dialog_with_currency(df_options = {}) {
		return cy.dialog({
			title: "Currency Check",
			animate: false,
			fields: [
				{
					fieldname: fieldname,
					fieldtype: "Currency",
					Label: "Currency",
					...df_options,
				},
			],
		});
	}

	it("check value changes", () => {
		const TEST_CASES = [
			{
				input: "10.101",
				df_options: { precision: 1 },
				blur_expected: "10.1",
			},
			{
				input: "10.101",
				df_options: { precision: "3" },
				blur_expected: "10.101",
			},
			{
				input: "10.101",
				df_options: { precision: "" }, // default assumed to be 2;
				blur_expected: "10.10",
			},
			{
				input: "10.101",
				df_options: { precision: "0" },
				blur_expected: "10",
			},
			{
				input: "10.101",
				df_options: { precision: 0 },
				blur_expected: "10",
			},
			{
				input: "10.000",
				number_format: "#.###,##",
				df_options: { precision: 0 },
				blur_expected: "10.000",
			},
			{
				input: "10.000",
				number_format: "#.###,##",
				blur_expected: "10.000,00",
			},
			{
				input: "10.101",
				df_options: { precision: "" },
				blur_expected: "10.1",
				default_precision: 1,
			},
		];

		TEST_CASES.forEach((test_case) => {
			cy.window()
				.its("saashq")
				.then((saashq) => {
					saashq.boot.sysdefaults.currency = test_case.currency;
					saashq.boot.sysdefaults.currency_precision = test_case.default_precision ?? 2;
					saashq.boot.sysdefaults.number_format = test_case.number_format ?? "#,###.##";
				});

			get_dialog_with_currency(test_case.df_options).as("dialog");
			cy.wait(300);
			cy.get_field(fieldname, "Currency").clear();
			cy.wait(300);
			cy.fill_field(fieldname, test_case.input, "Currency").blur();
			cy.get_field(fieldname, "Currency").should("have.value", test_case.blur_expected);
			cy.hide_dialog();
		});
	});
});
