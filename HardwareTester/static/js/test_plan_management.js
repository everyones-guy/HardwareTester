$(document).ready(function () {
    const testPlansList = $("#test-plans-list");
    const createTestPlanForm = $("#createTestPlanForm");
    const screenDropdown = $("#testPlanScreen");
    const eventDropdown = $("#testPlanEvent");
    const timingInput = $("#testPlanTiming");
    const saveTestPlanButton = $("#saveTestPlanButton");
    const loadExistingTestPlanButton = $("#loadExistingTestPlanButton");

    let currentPreviewPlanId = null;

    // Pre-populated options
    const defaultScreens = [
        "Configuration",
        "Main Page",
        "Administration",
        "Home",
        "Networking",
        "Provision",
        "Test",
    ];
    const defaultEvents = [
        "Button One",
        "Button Two",
        "Button Three",
        "Home",
        "Configuration",
        "Profile",
        "Provision",
        "Administration",
    ];

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

    // Populate dropdowns with default options
    function populateDropdown(dropdown, options) {
        dropdown.empty(); // Clear existing options
        dropdown.append('<option value="" disabled selected>Select an option</option>');
        options.forEach((option) => {
            dropdown.append(`<option value="${option.toLowerCase().replace(/\s+/g, "_")}">${option}</option>`);
        });
    }

    // Initialize dropdowns with default values
    populateDropdown(screenDropdown, defaultScreens);
    populateDropdown(eventDropdown, defaultEvents);

    // Add a new screen to the dropdown
    $("#addScreenButton").on("click", function () {
        const newScreen = prompt("Enter the name of the new screen:");
        if (newScreen) {
            const optionValue = newScreen.toLowerCase().replace(/\s+/g, "_");
            screenDropdown.append(`<option value="${optionValue}">${newScreen}</option>`);
            screenDropdown.val(optionValue); // Automatically select the new option
        }
    });

    // Add a new event to the dropdown
    $("#addEventButton").on("click", function () {
        const newEvent = prompt("Enter the name of the new event:");
        if (newEvent) {
            const optionValue = newEvent.toLowerCase().replace(/\s+/g, "_");
            eventDropdown.append(`<option value="${optionValue}">${newEvent}</option>`);
            eventDropdown.val(optionValue); // Automatically select the new option
        }
    });

    // Save the new test plan
    saveTestPlanButton.on("click", function () {
        const formData = {
            testPlanName: $("#testPlanName").val(),
            testPlanScreen: screenDropdown.val(),
            testPlanEvent: eventDropdown.val(),
            testPlanTiming: timingInput.val(),
            testPlanDescription: $("#testPlanDescription").val(),
        };

        if (!formData.testPlanName || !formData.testPlanScreen || !formData.testPlanEvent || !formData.testPlanTiming) {
            alert("All fields are required.");
            return;
        }

        apiCall(
            "/test-plans/create",
            "POST",
            formData,
            function (data) {
                if (data.success) {
                    alert("Test plan created successfully!");
                    createTestPlanForm[0].reset();
                    populateDropdown(screenDropdown, defaultScreens); // Reset dropdowns
                    populateDropdown(eventDropdown, defaultEvents);
                    $("#createTestPlanModal").modal("hide");
                } else {
                    alert(`Error: ${data.error}`);
                }
            },
            function (xhr) {
                console.error("Error creating test plan:", xhr.responseText);
            }
        );
    });
    // Load existing test plans
    loadExistingTestPlanButton.on("click", function () {
        apiCall(
            "/test-plans/list",
            "GET",
            {},
            function (data) {
                if (data.success && data.testPlans.length > 0) {
                    const testPlans = data.testPlans.map(
                        (plan) =>
                            `<li class="list-group-item d-flex justify-content-between align-items-center">
                                <span>${plan.name} - Uploaded by ${plan.uploaded_by}</span>
                                <button class="btn btn-sm btn-primary load-plan-btn" data-id="${plan.id}">Load</button>
                            </li>`
                    );
                    $("#existingTestPlanList").html(testPlans.join(""));
                    $("#existingTestPlanModal").modal("show");
                } else {
                    $("#existingTestPlanList").html(`<li class="list-group-item text-muted">No test plans available.</li>`);
                    $("#existingTestPlanModal").modal("show");
                }
            },
            function (xhr) {
                console.error("Error loading test plans:", xhr.responseText);
            }
        );
    });

    // Handle loading a specific test plan
    $("#existingTestPlanList").on("click", ".load-plan-btn", function () {
        const testPlanId = $(this).data("id");
        apiCall(
            `/test-plans/${testPlanId}/load`,
            "GET",
            {},
            function (data) {
                if (data.success) {
                    alert(`Test plan "${data.plan.name}" loaded successfully.`);
                    $("#existingTestPlanModal").modal("hide");
                } else {
                    alert(`Error: ${data.error}`);
                }
            },
            function (xhr) {
                console.error("Error loading test plan:", xhr.responseText);
            }
        );
    });


    // Initial load
    loadTestPlans();
});