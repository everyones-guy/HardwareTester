$(document).ready(function () {
    // CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";

    // Utility: Show alerts
    function showAlert(message, type = "success") {
        const alertContainer = $("#alert-container");
        alertContainer.html(
            `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>`
        );
        setTimeout(() => $(".alert").alert("close"), 5000); // Auto-dismiss after 5 seconds
    }

    // Fetch uploaded test plans and display them
    async function updateTestPlansList() {
        try {
            const data = await apiCall("/test-plans/list", "GET");
            const list = $("#test-plans-list");
            list.empty();

            if (data.success) {
                const plans = data.testPlans;
                if (plans.length > 0) {
                    plans.forEach((plan) => {
                        list.append(`
                            <li class="list-group-item">
                                <strong>${plan.name}</strong> - Uploaded by ${plan.uploaded_by}
                                <span class="badge bg-info float-end">ID: ${plan.id}</span>
                            </li>
                        `);
                    });
                } else {
                    list.append('<li class="list-group-item">No test plans uploaded yet.</li>');
                }
            } else {
                showAlert(data.message, "danger");
            }
        } catch (error) {
            console.error("Failed to load test plans:", error);
            showAlert("Error loading test plans.", "danger");
        }
    }

    // Handle test plan upload
    $("#upload-test-plan-form").on("submit", async function (event) {
        event.preventDefault();
        const formData = new FormData(this);

        try {
            const response = await apiCall("/upload-test-plan", "POST", formData, true); // Handles FormData correctly
            showAlert(response.message, "success");
            updateTestPlansList();
        } catch (error) {
            console.error("Test plan upload failed:", error);
            showAlert(error.error || "Failed to upload test plan.", "danger");
        }
    });

    // Handle Spec Sheet Upload
    $("#upload-spec-sheet-form").on("submit", async function (event) {
        event.preventDefault();
        const formData = new FormData(this);

        try {
            const response = await apiCall("/upload-spec-sheet", "POST", formData, true); // Handles FormData correctly

            if (response.success && response.generatedJson) {
                showAlert("Spec sheet processed successfully. Previewing JSON...");
                jsonEditor.set(response.generatedJson); // Populate JSON editor
            } else {
                showAlert(response.message || "Failed to process spec sheet.", "danger");
            }
        } catch (error) {
            console.error("Error processing spec sheet:", error);
            showAlert("An error occurred while processing the spec sheet.", "danger");
        }
    });

    // Emulate JSON Configuration
    $("#emulate-json-button").on("click", function () {
        try {
            const configuration = jsonEditor.get();
            validateConfiguration(configuration);

            startEmulation(configuration);
        } catch (err) {
            showAlert(err.message, "danger");
        }
    });

    // Real-Time Logging
    function setupSocketIO() {
        const socket = io();
        socket.on("log_message", (data) => {
            const logContainer = $("#real-time-logs");
            logContainer.append(`<div>${data.message}</div>`);
            logContainer.scrollTop(logContainer.prop("scrollHeight"));
        });
    }

    // Initialize
    setupSocketIO();
    updateTestPlansList();
});
