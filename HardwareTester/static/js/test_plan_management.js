$(document).ready(function () {
    const testPlansList = $("#test-plans-list");
    const testResults = $("#test-results");
    const previewSection = $("#test-plan-preview-section");
    const previewPlanName = $("#preview-plan-name");
    const previewUploadedBy = $("#preview-uploaded-by");
    const previewSteps = $("#preview-steps");
    const runPreviewPlanButton = $("#run-preview-plan");

    let currentPreviewPlanId = null;

    // Fetch and display test plans
    function loadTestPlans() {
        apiCall(
            "/test-plans/list",
            "GET",
            {},
            function (data) {
                testPlansList.empty(); // Clear the list first

                if (data.success && data.testPlans.length > 0) {
                    // Populate the list with test plans
                    data.testPlans.forEach((plan) => {
                        testPlansList.append(`
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${plan.name}</strong> - Uploaded by ${plan.uploaded_by}
                            </div>
                            <button class="btn btn-sm btn-secondary preview-plan-btn" data-id="${plan.id}">Preview</button>
                        </li>
                    `);
                    });
                } else {
                    // Display a message if no test plans are available
                    testPlansList.html(`<li class="list-group-item text-muted">No test plans available.</li>`);
                }
            },
            function (xhr) {
                console.error("Error loading test plans:", xhr.responseText);
                alert("Failed to load test plans.");
            }
        );
    }// Handle test plan upload
    $("#upload-test-plan-form").on("submit", function (event) {
        event.preventDefault();
        const formData = new FormData(this);

        // Note: FormData is passed directly to the API call
        apiCall(
            "/test-plans/upload",
            "POST",
            formData,
            function (data) {
                if (data.success) {
                    alert(data.message);
                    loadTestPlans();
                } else {
                    alert(`Error: ${data.error}`);
                }
            },
            function (xhr) {
                console.error("Error uploading test plan:", xhr.responseText);
            }
        );
    });

    // Preview a test plan
    testPlansList.on("click", ".preview-plan-btn", function () {
        const testPlanId = $(this).data("id");

        apiCall(
            `/test-plans/${testPlanId}/preview`,
            "GET",
            {},
            function (data) {
                if (data.success) {
                    currentPreviewPlanId = testPlanId;
                    previewPlanName.text(data.plan.name);
                    previewUploadedBy.text(data.plan.uploaded_by);
                    previewSteps.html(
                        data.plan.steps
                            .map(
                                (step, index) =>
                                    `<li class="list-group-item">Step ${index + 1}: ${step.description}</li>`
                            )
                            .join("")
                    );
                    previewSection.removeClass("d-none");
                } else {
                    alert(data.error);
                }
            },
            function (xhr) {
                console.error("Error fetching test plan preview:", xhr.responseText);
            }
        );
    });

    // Run the previewed test plan
    runPreviewPlanButton.on("click", function () {
        if (currentPreviewPlanId) {
            apiCall(
                `/test-plans/run/${currentPreviewPlanId}`,
                "POST",
                {},
                function (data) {
                    testResults.empty();
                    if (data.success) {
                        const resultsHTML = data.results
                            .map((result) => `<li>${result.step.Step}: ${result.result}</li>`)
                            .join("");
                        testResults.html(`<ul>${resultsHTML}</ul>`);
                    } else {
                        testResults.html(`<p class="text-danger">${data.error}</p>`);
                    }
                },
                function (xhr) {
                    console.error("Error running test plan:", xhr.responseText);
                }
            );
        }
    });

    // Initial load
    loadTestPlans();
});