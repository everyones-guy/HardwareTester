
// Fetch and display system summary
function loadSystemSummary() {
    $.getJSON("/system-status/summary", function (data) {
        const summary = $("#system-summary");
        summary.empty();
        if (data.success) {
            const status = data.status;
            summary.append(`<li class="list-group-item"><strong>Hostname:</strong> ${status.hostname}</li>`);
            summary.append(`<li class="list-group-item"><strong>OS:</strong> ${status.os} ${status.os_version}</li>`);
            summary.append(`<li class="list-group-item"><strong>CPU Usage:</strong> ${status.cpu_usage}%</li>`);
            summary.append(`<li class="list-group-item"><strong>Memory Usage:</strong> ${status.memory_usage}%</li>`);
            summary.append(`<li class="list-group-item"><strong>Disk Usage:</strong> ${status.disk_usage}%</li>`);
            summary.append(`<li class="list-group-item"><strong>Uptime:</strong> ${status.uptime}</li>`);
        } else {
            summary.append(`<li class="list-group-item text-danger">${data.error}</li>`);
        }
    });
}

// Fetch and display detailed metrics
function loadSystemMetrics() {
    $.getJSON("/system-status/metrics", function (data) {
        const metrics = $("#system-metrics");
        metrics.empty();
        if (data.success) {
            const details = data.metrics;
            metrics.append(`<li class="list-group-item"><strong>CPU Count:</strong> ${details.cpu_count}</li>`);
            metrics.append(`<li class="list-group-item"><strong>CPU Frequency:</strong> ${details.cpu_freq.current} MHz</li>`);
            metrics.append(`<li class="list-group-item"><strong>Total Memory:</strong> ${(details.memory.total / 1e9).toFixed(2)} GB</li>`);
            metrics.append(`<li class="list-group-item"><strong>Used Memory:</strong> ${(details.memory.used / 1e9).toFixed(2)} GB (${details.memory.percent}%)</li>`);
            metrics.append(`<li class="list-group-item"><strong>Available Memory:</strong> ${(details.memory.available / 1e9).toFixed(2)} GB</li>`);

            metrics.append("<li class='list-group-item'><strong>Disk Partitions:</strong></li>");
            details.disk_partitions.forEach((partition) => {
                metrics.append(`<li class="list-group-item">Device: ${partition.device}, Usage: ${partition.usage.percent}%</li>`);
            });

            metrics.append("<li class='list-group-item'><strong>Network IO:</strong></li>");
            metrics.append(`<li class="list-group-item">Bytes Sent: ${(details.network.io_counters.bytes_sent / 1e6).toFixed(2)} MB</li>`);
            metrics.append(`<li class="list-group-item">Bytes Received: ${(details.network.io_counters.bytes_recv / 1e6).toFixed(2)} MB</li>`);
        } else {
            metrics.append(`<li class="list-group-item text-danger">${data.error}</li>`);
        }
    });
}

// Load data on page load
$(document).ready(function () {
    loadSystemSummary();
    loadSystemMetrics();
});

