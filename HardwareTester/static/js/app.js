// Utility function to display alerts
function showAlert(message, type = "success") {
    const alertContainer = $("#alert-container");
    alertContainer.html(
        `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>`
    );
}

// Utility function to append logs to a real-time log viewer
function appendLog(message) {
    const logContainer = $("#real-time-logs");
    logContainer.append(`<div>${message}</div>`);
    logContainer.scrollTop(logContainer.prop("scrollHeight"));
}

// Real-time log updates using Socket.IO
function setupSocketIO() {
    const socket = io();
    socket.on("log_message", (data) => appendLog(data.message));
}

// Fetch uploaded test plans and display them
function updateTestPlansList() {
    $.get("/get-uploaded-test-plans")
        .done(function (data) {
            const list = $("#uploaded-test-plans-list");
            list.empty();

            if (data.success) {
                const plans = data.testPlans;
                if (plans.length > 0) {
                    plans.forEach(plan => {
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
        })
        .fail(() => showAlert("Failed to fetch test plans.", "danger"));
}

// Fetch list of valves and display them
function updateValveList() {
    $.get("/get-valves")
        .done(function (data) {
            const list = $("#valve-list");
            list.empty();

            if (data.success) {
                const valves = data.valves;
                if (valves.length > 0) {
                    valves.forEach(valve => {
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
        })
        .fail(() => showAlert("Failed to fetch valves.", "danger"));
}

// Fetch valve statuses and display them
function refreshValveStatus() {
    $.get("/get-valve-status")
        .done(function (data) {
            const container = $("#valve-status-container");
            container.empty();

            if (data.success) {
                const statuses = data.statuses;
                statuses.forEach(status => {
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
        })
        .fail(() => showAlert("Failed to fetch valve statuses.", "danger"));
}

// Handle test plan upload form submission
function handleTestPlanUpload() {
    $("#upload-test-plan-form").on("submit", function (event) {
        event.preventDefault();
        const formData = new FormData(this);

        $.ajax({
            url: "/upload-test-plan",
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
        })
            .done(function (response) {
                showAlert(response.message, "success");
                updateTestPlansList();
            })
            .fail(function (xhr) {
                const errorMessage = xhr.responseJSON?.message || "An error occurred.";
                showAlert(errorMessage, "danger");
            });
    });
}

// Handle spec sheet upload form submission
function handleSpecSheetUpload() {
    $("#upload-spec-sheet-form").on("submit", function (event) {
        event.preventDefault();
        const formData = new FormData(this);

        $.ajax({
            url: "/upload-spec-sheet",
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
        })
            .done(function (response) {
                showAlert(response.message, "success");
                updateValveList();
            })
            .fail(function (xhr) {
                const errorMessage = xhr.responseJSON?.message || "An error occurred.";
                showAlert(errorMessage, "danger");
            });
    });
}

// Handle test plan execution form submission
function handleTestPlanExecution() {
    $("#run-test-plan-form").on("submit", function (event) {
        event.preventDefault();
        const testPlanId = $("#testPlanId").val();

        $.post(`/run-test-plan/${testPlanId}`)
            .done(function (data) {
                if (data.success) {
                    let resultsHtml = "<ul>";
                    data.results.forEach(result => {
                        resultsHtml += `<li>${result.step.Step}: ${result.result}</li>`;
                    });
                    resultsHtml += "</ul>";
                    $("#run-test-plan-results").html(resultsHtml);
                } else {
                    showAlert(data.message, "danger");
                }
            })
            .fail(() => showAlert("Failed to execute test plan.", "danger"));
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
