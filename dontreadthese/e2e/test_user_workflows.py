describe("E2E: User Workflows", () => {
    it("uploads a spec sheet successfully", () => {
        cy.visit("/valve-management");
        cy.get("#specSheetFile").attachFile("test_spec.pdf");
        cy.get("#upload-spec-sheet-form").submit();
        cy.contains("Spec sheet uploaded successfully!");
    });

    it("displays valve statuses", () => {
        cy.visit("/valve-management");
        cy.get("#valve-status-container").should("not.be.empty");
    });

    it("executes a test plan", () => {
        cy.visit("/run-test-plan");
        cy.get("#testPlanId").type("1");
        cy.get("#run-test-plan-form").submit();
        cy.contains("Test Plan executed successfully!");
    });
});
