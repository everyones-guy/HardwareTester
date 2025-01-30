import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import Chart from "chart.js/auto";

const HardwareLogsMetrics = () => {
    // State Hooks
    const [logs, setLogs] = useState([]);
    const [metrics, setMetrics] = useState({});
    const [filters, setFilters] = useState({ severity: "all", search: "", dateRange: null });
    const [isStreaming, setIsStreaming] = useState(true);
    const [chartInstance, setChartInstance] = useState(null);
    const logStream = useRef(null);

    // Fetch logs & metrics on mount
    useEffect(() => {
        fetchLogs();
        fetchMetrics();
        if (isStreaming) {
            startLogStream();
        }
        return () => stopLogStream();
    }, []);

    // Fetch historical logs
    const fetchLogs = async () => {
        try {
            const response = await axios.get("/api/hardware/logs");
            setLogs(response.data);
        } catch (error) {
            console.error("Error fetching logs:", error);
        }
    };

    // Fetch system metrics
    const fetchMetrics = async () => {
        try {
            const response = await axios.get("/api/hardware/metrics");
            setMetrics(response.data);
            updateChart(response.data);
        } catch (error) {
            console.error("Error fetching metrics:", error);
        }
    };

    // Real-time log streaming
    const startLogStream = () => {
        logStream.current = new EventSource("/api/hardware/log-stream");

        logStream.current.onmessage = (event) => {
            setLogs((prevLogs) => [JSON.parse(event.data), ...prevLogs]);
        };

        logStream.current.onerror = () => {
            console.error("Log stream error.");
            stopLogStream();
        };
    };

    // Stop streaming logs
    const stopLogStream = () => {
        if (logStream.current) logStream.current.close();
    };

    // Handle filtering
    const filteredLogs = logs.filter((log) => {
        const matchesSeverity = filters.severity === "all" || log.severity === filters.severity;
        const matchesSearch = log.message.toLowerCase().includes(filters.search.toLowerCase());
        return matchesSeverity && matchesSearch;
    });

    // Generate Chart
    const updateChart = (data) => {
        const ctx = document.getElementById("hardwareMetricsChart");
        if (chartInstance) chartInstance.destroy();

        const newChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: data.timestamps,
                datasets: [
                    { label: "CPU Usage (%)", data: data.cpuUsage, borderColor: "red", fill: false },
                    { label: "Memory Usage (MB)", data: data.memoryUsage, borderColor: "blue", fill: false },
                    { label: "I/O Throughput (KB/s)", data: data.ioThroughput, borderColor: "green", fill: false },
                ],
            },
            options: { responsive: true, maintainAspectRatio: false },
        });

        setChartInstance(newChart);
    };

    return (
        <div className="hardware-logs-metrics">
            <h1>Real-Time Hardware Logs & Metrics</h1>

            {/* Control Panel */}
            <div>
                <button onClick={() => (isStreaming ? stopLogStream() : startLogStream())}>
                    {isStreaming ? "Pause Logging" : "Resume Logging"}
                </button>
                <button onClick={fetchLogs}>Refresh Logs</button>
                <button onClick={fetchMetrics}>Refresh Metrics</button>
            </div>

            {/* Filters */}
            <div>
                <label>Search Logs:</label>
                <input type="text" value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} />
                <label>Severity:</label>
                <select value={filters.severity} onChange={(e) => setFilters({ ...filters, severity: e.target.value })}>
                    <option value="all">All</option>
                    <option value="info">Info</option>
                    <option value="warning">Warning</option>
                    <option value="error">Error</option>
                </select>
            </div>

            {/* Logs Table */}
            <div>
                <h3>Live Logs</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Severity</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredLogs.map((log, index) => (
                            <tr key={index}>
                                <td>{log.timestamp}</td>
                                <td>{log.severity}</td>
                                <td>{log.message}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Metrics Graph */}
            <div>
                <h3>System Metrics</h3>
                <canvas id="hardwareMetricsChart"></canvas>
            </div>

            {/* Export Buttons */}
            <div>
                <button onClick={() => exportData("csv")}>Export CSV</button>
                <button onClick={() => exportData("json")}>Export JSON</button>
                <button onClick={() => exportData("pdf")}>Export PDF</button>
            </div>
        </div>
    );
};

export default HardwareLogsMetrics;
