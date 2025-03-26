$(document).ready(function () {
    const logContainer = $("#log-container");
    const logPagination = $("#log-pagination");
    const logFilters = {
        level: $("#log-level"),
        keyword: $("#log-keyword"),
        startDate: $("#log-start-date"),
        endDate: $("#log-end-date"),
    };
    const logsPerPage = 20;
    let currentPage = 1;

    /**
     * Fetch and display logs
     */
    async function fetchLogs(page = 1, filters = {}) {
        try {
            const data = await apiCall(`/logs?page=${page}&limit=${logsPerPage}`, "GET", filters);

            logContainer.empty();
            logPagination.empty();

            if (data.success) {
                if (data.logs.length > 0) {
                    data.logs.forEach((log, index) => {
                        const logEntry = `
                            <div class="log-entry ${index % 2 === 0 ? "log-even" : "log-odd"}">
                                <strong class="log-level">${log.level}</strong> 
                                <span class="log-timestamp">[${log.timestamp}]</span>: 
                                <span class="log-message">${log.message}</span>
                                <pre class="log-context">${log.context || ""}</pre>
                            </div>
                            <hr>
                        `;
                        logContainer.append(logEntry);
                    });

                    renderPagination(data.totalPages, page);
                } else {
                    logContainer.html("<p class='text-muted'>No logs found for selected filters.</p>");
                }
            } else {
                logContainer.html("<p class='text-danger'>Failed to load logs.</p>");
            }
        } catch (error) {
            console.error("Error fetching logs:", error);
            logContainer.html("<p class='text-danger'>An unexpected error occurred.</p>");
        }
    }

    /**
     * Render pagination controls
     */
    function renderPagination(totalPages, currentPage) {
        logPagination.empty();
        for (let i = 1; i <= totalPages; i++) {
            const activeClass = i === currentPage ? "active" : "";
            logPagination.append(`<li class="page-item ${activeClass}"><a class="page-link" href="#">${i}</a></li>`);
        }

        $(".page-link").on("click", function (event) {
            event.preventDefault();
            const page = $(this).text();
            currentPage = parseInt(page);
            fetchLogs(currentPage, getFilters());
        });
    }

    /**
     * Get filter values
     */
    function getFilters() {
        return {
            level: logFilters.level.val(),
            keyword: logFilters.keyword.val(),
            start_date: logFilters.startDate.val(),
            end_date: logFilters.endDate.val(),
        };
    }

    /**
     * Apply filters and fetch logs
     */
    $("#filter-logs").on("click", function () {
        fetchLogs(1, getFilters());
    });

    /**
     * WebSocket Real-time log updates
     */
    const socket = io("/logs");
    socket.on("new_log", (log) => {
        const newLogEntry = `
            <div class="log-entry new-log">
                <strong class="log-level">${log.level}</strong> 
                <span class="log-timestamp">[${log.timestamp}]</span>: 
                <span class="log-message">${log.message}</span>
                <pre class="log-context">${log.context || ""}</pre>
            </div>
            <hr>
        `;
        logContainer.prepend(newLogEntry);
    });

    // Initial load
    fetchLogs();
});
