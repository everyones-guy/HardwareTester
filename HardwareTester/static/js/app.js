$(document).ready(function () {
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

    // Utility: Append logs to the real-time log viewer
    function appendLog(message) {
        const logContainer = $("#real-time-logs");
        logContainer.append(`<div>${message}</div>`);
        logContainer.scrollTop(logContainer.prop("scrollHeight"));
    }

    // Utility: Centralized API call function
    function apiCall(endpoint, method = "GET", data = null, onSuccess = null, onError = null) {
        $.ajax({
            url: endpoint,
            type: method,
            contentType: method === "GET" ? undefined : "application/json",
            headers: { "X-CSRFToken": csrfToken },
            data: method === "GET" ? null : JSON.stringify(data),
            processData: false,
            success: (response) => {
                if (onSuccess) onSuccess(response);
            },
            error: (xhr) => {
                const errorMessage = xhr.responseJSON?.message || "An error occurred.";
                showAlert(errorMessage, "danger");
                if (onError) onError(xhr);
            },
        });
    }

    // Real-time logging setup using Socket.IO
    function setupSocketIO() {
        const socket = io();
        socket.on("log_message", (data) => appendLog(data.message));
    }

    // Fetch and display valves
    function updateValveList() {
        apiCall("/valves/list", "GET", null, (data) => {
            const list = $("#valve-list");
            list.empty();

            if (data.success) {
                data.valves.forEach((valve) => {
                    list.append(`
                        <li class="list-group-item">
                            <strong>${valve.name}</strong> - ${valve.type}
                            <button class="btn btn-danger btn-sm float-end delete-valve" data-id="${valve.id}">Delete</button>
                            <button class="btn btn-secondary btn-sm float-end update-valve me-2" data-id="${valve.id}">Update</button>
                        </li>
                    `);
                });
            } else {
                showAlert(data.message, "danger");
            }
        });
    }

    // Add a new valve
    $("#add-valve-form").on("submit", function (event) {
        event.preventDefault();
        const formData = new FormData(this);

        apiCall("/valves/add", "POST", Object.fromEntries(formData), (response) => {
            showAlert(response.message, "success");
            updateValveList();
        });
    });

    // Delete a valve
    $("#valve-list").on("click", ".delete-valve", function () {
        const valveId = $(this).data("id");

        apiCall(`/valves/${valveId}/delete`, "DELETE", null, (response) => {
            showAlert(response.message, "success");
            updateValveList();
        });
    });

    // Update a valve
    $("#valve-list").on("click", ".update-valve", function () {
        const valveId = $(this).data("id");
        const newName = prompt("Enter new name for the valve:");
        const newType = prompt("Enter new type for the valve:");
        const newSpecs = prompt("Enter new specifications for the valve:");

        if (newName && newType && newSpecs) {
            const data = { name: newName, type: newType, specifications: newSpecs };

            apiCall(`/valves/${valveId}/update`, "PUT", data, (response) => {
                showAlert(response.message, "success");
                updateValveList();
            });
        } else {
            showAlert("Update canceled. All fields are required.", "warning");
        }
    });

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

    // Initialize
    setupSocketIO();
    updateTestPlansList();
    updateValveList();

    // Refresh valve statuses
    $("#refresh-valve-status").on("click", updateValveList);
});
