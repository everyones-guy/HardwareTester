document.addEventListener("DOMContentLoaded", () => {
    const logContainer = document.getElementById("log-container");

    // Fetch and display logs
    function fetchLogs(filters = {}) {
        fetch("/logs", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').getAttribute("content"),
            },
            body: JSON.stringify(filters),
        })
            .then(response => response.json())
            .then(data => {
                logContainer.innerHTML = "";
                if (data.success) {
                    data.logs.forEach(log => {
                        const logEntry = `
                            <div class="log-entry">
                                <strong>${log.level}</strong> [${log.timestamp}]: ${log.message}
                                <pre>${log.context || ""}</pre>
                            </div>
                            <hr>
                        `;
                        logContainer.insertAdjacentHTML("beforeend", logEntry);
                    });
                } else {
                    logContainer.innerHTML = "<p class='text-danger'>Failed to load logs.</p>";
                }
            })
            .catch(error => {
                console.error("Error fetching logs:", error);
                logContainer.innerHTML = "<p class='text-danger'>An unexpected error occurred.</p>";
            });
    }

    // Apply filters
    document.getElementById("filter-logs").addEventListener("click", () => {
        const filters = {
            level: document.getElementById("log-level").value,
            keyword: document.getElementById("log-keyword").value,
            start_date: document.getElementById("log-start-date").value,
            end_date: document.getElementById("log-end-date").value,
        };
        fetchLogs(filters);
    });

    // Initial load
    fetchLogs();
});
