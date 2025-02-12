document.addEventListener("DOMContentLoaded", () => {
    const systemSummary = document.getElementById("system-summary");
    const systemMetrics = document.getElementById("system-metrics");

    /**
     * Fetch and display system summary.
     */
    async function loadSystemSummary() {
        systemSummary.innerHTML = "<li class='list-group-item'>Loading system summary...</li>";

        try {
            const data = await apiCall("/system-status/summary", "GET");

            systemSummary.innerHTML = "";
            if (data.success) {
                const status = data.status;
                systemSummary.innerHTML = `
                    <li class="list-group-item"><strong>Hostname:</strong> ${status.hostname}</li>
                    <li class="list-group-item"><strong>OS:</strong> ${status.os} ${status.os_version}</li>
                    <li class="list-group-item"><strong>CPU Usage:</strong> ${status.cpu_usage}%</li>
                    <li class="list-group-item"><strong>Memory Usage:</strong> ${status.memory_usage}%</li>
                    <li class="list-group-item"><strong>Disk Usage:</strong> ${status.disk_usage}%</li>
                    <li class="list-group-item"><strong>Uptime:</strong> ${status.uptime}</li>`;
            } else {
                systemSummary.innerHTML = `<li class="list-group-item text-danger">${data.error}</li>`;
            }
        } catch (error) {
            console.error("Error fetching system summary:", error);
            systemSummary.innerHTML = `<li class="list-group-item text-danger">Failed to load system summary.</li>`;
        }
    }

    /**
     * Fetch and display detailed system metrics.
     */
    async function loadSystemMetrics() {
        systemMetrics.innerHTML = "<li class='list-group-item'>Loading system metrics...</li>";

        try {
            const data = await apiCall("/system-status/metrics", "GET");

            systemMetrics.innerHTML = "";
            if (data.success) {
                const details = data.metrics;
                systemMetrics.innerHTML = `
                    <li class="list-group-item"><strong>CPU Count:</strong> ${details.cpu_count}</li>
                    <li class="list-group-item"><strong>CPU Frequency:</strong> ${details.cpu_freq.current} MHz</li>
                    <li class="list-group-item"><strong>Total Memory:</strong> ${(details.memory.total / 1e9).toFixed(2)} GB</li>
                    <li class="list-group-item"><strong>Used Memory:</strong> ${(details.memory.used / 1e9).toFixed(2)} GB (${details.memory.percent}%)</li>
                    <li class="list-group-item"><strong>Available Memory:</strong> ${(details.memory.available / 1e9).toFixed(2)} GB</li>
                    <li class="list-group-item"><strong>Network Traffic:</strong></li>
                    <li class="list-group-item">Bytes Sent: ${(details.network.io_counters.bytes_sent / 1e6).toFixed(2)} MB</li>
                    <li class="list-group-item">Bytes Received: ${(details.network.io_counters.bytes_recv / 1e6).toFixed(2)} MB</li>
                    <li class="list-group-item"><strong>Disk Partitions:</strong></li>`;

                details.disk_partitions.forEach((partition) => {
                    systemMetrics.innerHTML += `
                        <li class="list-group-item">Device: ${partition.device}, Usage: ${partition.usage.percent}%</li>`;
                });
            } else {
                systemMetrics.innerHTML = `<li class="list-group-item text-danger">${data.error}</li>`;
            }
        } catch (error) {
            console.error("Error fetching system metrics:", error);
            systemMetrics.innerHTML = `<li class="list-group-item text-danger">Failed to load system metrics.</li>`;
        }
    }

    // Load data on page load
    loadSystemSummary();
    loadSystemMetrics();
});
