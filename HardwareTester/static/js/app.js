
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

// Utility function to display alerts
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

// Utility function to append logs to a real-time log viewer
function appendLog(message) {
    const logContainer = $("#real-time-logs");
    logContainer.append(`<div>${message}</div>`);
    logContainer.scrollTop(logContainer.prop("scrollHeight"));
}

// Utility function for AJAX requests
function ajaxRequest(url, method = "GET", data = null, successCallback, errorCallback) {
    $.ajax({
        url,
        method,
        data,
        headers: {
            "X-CSRFToken": csrfToken  // Ensure CSRF token is sent
        },
        processData: false,
        contentType: false,
    })
        .done(successCallback)
        .fail((xhr) => {
            const errorMessage = xhr.responseJSON?.message || "An error occurred.";
            showAlert(errorMessage, "danger");
            if (errorCallback) errorCallback(xhr);
        });
}

// Real-time log updates using Socket.IO
function setupSocketIO() {
    const socket = io();
    socket.on("log_message", (data) => appendLog(data.message));
}

// Fetch uploaded test plans and display them
function updateTestPlansList() {
    ajaxRequest(
        "/get-uploaded-test-plans",
        "GET",
        null,
        function (data) {
            const list = $("#uploaded-test-plans-list");
            list.empty();

            if (data.success) {
                const plans = data.testPlans;
                if (plans.length > 0) {
                    plans.forEach((plan) => {
                        list.append(
                            `<li class="list-group-item">
                                <strong>${plan.name}</strong> - Uploaded by ${plan.uploaded_by}
                                <span class="badge bg-info float-end">ID: ${plan.id}</span>
                            </li>`
                        );
                    });
                } else {
                    list.append('<li class="list-group-item">No test plans uploaded yet.</li>');
                }
            } else {
                showAlert(data.message, "danger");
            }
        }
    );
}

// Fetch list of valves and display them
function updateValveList() {
    ajaxRequest(
        "/get-valves",
        "GET",
        null,
        function (data) {
            const list = $("#valve-list");
            list.empty();

            if (data.success) {
                const valves = data.valves;
                if (valves.length > 0) {
                    valves.forEach((valve) => {
                        list.append(
                            `<li class="list-group-item">
                                <strong>${valve.name}</strong> - ${valve.type}
                                <span class="badge bg-info float-end">ID: ${valve.id}</span>
                            </li>`
                        );
                    });
                } else {
                    list.append('<li class="list-group-item">No valves found.</li>');
                }
            } else {
                showAlert(data.message, "danger");
            }
        }
    );
}

// Fetch valve statuses and display them
function refreshValveStatus() {
    ajaxRequest(
        "/get-valve-status",
        "GET",
        null,
        function (data) {
            const container = $("#valve-status-container");
            container.empty();

            if (data.success) {
                const statuses = data.statuses;
                statuses.forEach((status) => {
                    container.append(
                        `<div>
                            <strong>Valve ${status.id}</strong>: ${status.status}
                            <small class="text-muted">(Last updated: ${status.last_updated})</small>
                        </div>`
                    );
                });
            } else {
                showAlert(data.message, "danger");
            }
        }
    );
}

// Handle test plan upload form submission
function handleTestPlanUpload() {
    $("#upload-test-plan-form").on("submit", function (event) {
        event.preventDefault();
        const formData = new FormData(this);
        ajaxRequest(
            "/upload-test-plan",
            "POST",
            formData,
            function (response) {
                showAlert(response.message, "success");
                updateTestPlansList();
            }
        );
    });
}

// Handle spec sheet upload form submission
function handleSpecSheetUpload() {
    $("#upload-spec-sheet-form").on("submit", function (event) {
        event.preventDefault();
        const formData = new FormData(this);
        ajaxRequest(
            "/upload-spec-sheet",
            "POST",
            formData,
            function (response) {
                showAlert(response.message, "success");
                updateValveList();
            }
        );
    });
}

// Handle test plan execution form submission
function handleTestPlanExecution() {
    $("#run-test-plan-form").on("submit", function (event) {
        event.preventDefault();
        const testPlanId = $("#testPlanId").val();

        ajaxRequest(
            `/run-test-plan/${testPlanId}`,
            "POST",
            null,
            function (data) {
                if (data.success) {
                    let resultsHtml = "<ul>";
                    data.results.forEach((result) => {
                        resultsHtml += `<li>${result.step.Step}: ${result.result}</li>`;
                    });
                    resultsHtml += "</ul>";
                    $("#run-test-plan-results").html(resultsHtml);
                } else {
                    showAlert(data.message, "danger");
                }
            }
        );
    });
}

// Initialize all functions on document ready
$(document).ready(function () {
    // Set up real-time logging
    setupSocketIO();

    // Initialize dynamic updates
    updateTestPlansList();
    updateValveList();
    refreshValveStatus();

    // Set up form handlers
    handleTestPlanUpload();
    handleSpecSheetUpload();
    handleTestPlanExecution();

    // Refresh valve statuses on button click
    $("#refresh-valve-status").click(refreshValveStatus);
});

