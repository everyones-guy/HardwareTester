$(document).ready(function () {
    const logContainer = $("#log-container");

    // Fetch and display logs
    function fetchLogs(filters = {}) {
        $.ajax({
            url: "/logs",
            method: "GET",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": $("meta[name='csrf-token']").attr("content"),
            },
            data: filters,
            success: function (data) {
                logContainer.empty();
                if (data.success) {
                    data.logs.forEach(function (log) {
                        const logEntry = `
                            <div class="log-entry">
                                <strong>${log.level}</strong> [${log.timestamp}]: ${log.message}
                                <pre>${log.context || ""}</pre>
                            </div>
                            <hr>
                        `;
                        logContainer.append(logEntry);
                    });
                } else {
                    logContainer.html("<p class='text-danger'>Failed to load logs.</p>");
                }
            },
            error: function (xhr) {
                console.error("Error fetching logs:", xhr);
                logContainer.html("<p class='text-danger'>An unexpected error occurred.</p>");
            },
        });
    }

    // Apply filters
    $("#filter-logs").on("click", function () {
        const filters = {
            level: $("#log-level").val(),
            keyword: $("#log-keyword").val(),
            start_date: $("#log-start-date").val(),
            end_date: $("#log-end-date").val(),
        };
        fetchLogs(filters);
    });

    // Initial load
    fetchLogs();
});