$(document).ready(function () {
    // CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

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
    function updateTestPlansList() {
        apiCall("/test-plans/list", "GET", null, (data) => {
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
        });
    }

    // Handle test plan upload
    $("#upload-test-plan-form").on("submit", function (event) {
        event.preventDefault();
        const formData = new FormData(this);

        apiCall("/upload-test-plan", "POST", Object.fromEntries(formData), (response) => {
            showAlert(response.message, "success");
            updateTestPlansList();
        });
    });

    // Handle Spec Sheet Upload
    function handleSpecSheetUpload() {
        $("#upload-spec-sheet-form").on("submit", async function (event) {
            event.preventDefault();
            const formData = new FormData(this);

            try {
                // Upload spec sheet and generate JSON
                const response = await fetch("/upload-spec-sheet", {
                    method: "POST",
                    headers: { "X-CSRFToken": csrfToken },
                    body: formData,
                });
                const data = await response.json();

                if (data.success && data.generatedJson) {
                    showAlert("Spec sheet processed successfully. Previewing JSON...");
                    jsonEditor.set(data.generatedJson); // Populate JSON editor with generated data
                } else {
                    showAlert(data.message || "Failed to process spec sheet.", "danger");
                }
            } catch (error) {
                console.error("Error processing spec sheet:", error);
                showAlert("An error occurred while processing the spec sheet.", "danger");
            }
        });
    }

    // Emulate JSON Configuration
    function emulateJsonConfiguration() {
        $("#emulate-json-button").on("click", function () {
            try {
                const configuration = jsonEditor.get();
                validateConfiguration(configuration);

                startEmulation(configuration);
            } catch (err) {
                showAlert(err.message, "danger");
            }
        });
    }

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
