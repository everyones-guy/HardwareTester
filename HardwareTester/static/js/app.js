// Utility function to display alerts
function showAlert(message, type = "success", autoClose = true, duration = 5000) {
    const alertContainer = $("#alert-container");
    alertContainer.html(
        `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>`
    );
    if (autoClose) setTimeout(() => $(".alert").alert("close"), duration); // Auto-dismiss
}

// Utility function to append logs
function appendLog(message) {
    const logContainer = $("#real-time-logs");
    logContainer.append(`<div>${message}</div>`);
    logContainer.scrollTop(logContainer.prop("scrollHeight"));
}

// Centralized AJAX request handler
function ajaxRequest(url, method = "GET", data = null, successCallback, errorCallback) {
    $.ajax({
        url,
        method,
        data,
        processData: false,
        contentType: false,
    })
        .done(successCallback)
        .fail((xhr) => {
            const errorMessage = xhr.responseJSON?.message || "An unexpected error occurred.";
            showAlert(errorMessage, "danger");
            console.error(`Error during AJAX request: ${errorMessage}`);
            if (errorCallback) errorCallback(xhr);
        });
}

// Real-time Socket.IO integration
function setupSocketIO() {
    const socket = io();

    // Real-time log updates
    socket.on("log_message", (data) => appendLog(data.message));

    // Real-time notifications
    socket.on("notification", (data) => {
        showAlert(data.message, "info");
        updateNotifications();
    });

    // System status updates
    socket.on("system_status", (data) => updateSystemStatus(data));
}

// Update dynamic notifications
function updateNotifications() {
    ajaxRequest("/api/notifications", "GET", null, (data) => {
        const notificationList = $("#notification-list");
        notificationList.empty();
        if (data.success) {
            data.notifications.forEach((notification) => {
                notificationList.append(`<li>${notification.message} - <small>${notification.date}</small></li>`);
            });
        } else {
            notificationList.append("<li>No notifications available.</li>");
        }
    });
}

// Update system status
function updateSystemStatus(status = null) {
    if (status) {
        // Use real-time data
        renderSystemStatus(status);
    } else {
        // Fetch status from API
        ajaxRequest("/api/system-status", "GET", null, (data) => {
            if (data.success) renderSystemStatus(data);
        });
    }
}

// Render system status on the page
function renderSystemStatus(data) {
    const statusContainer = $("#system-status-container");
    statusContainer.html(`
        <p><strong>CPU Usage:</strong> ${data.cpu}%</p>
        <p><strong>Memory Usage:</strong> ${data.memory}%</p>
        <p><strong>Disk Space:</strong> ${data.disk}</p>
    `);
}

// Update reports
function updateReports() {
    ajaxRequest("/api/reports", "GET", null, (data) => {
        const reportTable = $("#report-table tbody");
        reportTable.empty();
        if (data.success) {
            data.reports.forEach((report) => {
                reportTable.append(`
                    <tr>
                        <td>${report.name}</td>
                        <td>${report.date}</td>
                        <td>${report.status}</td>
                        <td><a href="${report.link}" target="_blank">View</a></td>
                    </tr>
                `);
            });
        } else {
            reportTable.append("<tr><td colspan='4'>No reports available.</td></tr>");
        }
    });
}

// Initialize the app on document ready
$(document).ready(function () {
    // Initialize real-time socket updates
    setupSocketIO();

    // Fetch and update dynamic data
    updateTestPlansList();
    updateValveList();
    refreshValveStatus();
    updateNotifications();
    updateReports();
    updateSystemStatus();

    // Setup form handlers
    handleTestPlanUpload();
    handleSpecSheetUpload();
    handleTestPlanExecution();

    // Refresh statuses periodically
    setInterval(refreshValveStatus, 30000); // Refresh valve status every 30 seconds
});
