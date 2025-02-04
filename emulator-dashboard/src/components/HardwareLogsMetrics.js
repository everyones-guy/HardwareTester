import React, { useState, useEffect } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

const HardwareLogsMetrics = () => {
    // State Hooks
    const [logs, setLogs] = useState([]);
    const [metrics, setMetrics] = useState([]);
    const [filters, setFilters] = useState({ severity: "all", search: "" });
    const [isStreaming, setIsStreaming] = useState(true);

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
            const formattedData = response.data.timestamps.map((timestamp, index) => ({
                timestamp,
                cpuUsage: response.data.cpuUsage[index],
                memoryUsage: response.data.memoryUsage[index],
                ioThroughput: response.data.ioThroughput[index]
            }));
            setMetrics(formattedData);
        } catch (error) {
            console.error("Error fetching metrics:", error);
        }
    };

    // Real-time log streaming (if needed)
    const startLogStream = () => {
        console.log("Streaming logs...");
        // Add EventSource or MQTT integration if needed
    };

    // Stop streaming logs
    const stopLogStream = () => {
        console.log("Stopped streaming logs.");
    };

    // Handle filtering
    const filteredLogs = logs.filter((log) => {
        const matchesSeverity = filters.severity === "all" || log.severity === filters.severity;
        const matchesSearch = log.message.toLowerCase().includes(filters.search.toLowerCase());
        return matchesSeverity && matchesSearch;
    });

    return (
        <div className="hardware-logs-metrics">
            <h1>Real-Time Hardware Logs & Metrics</h1>

            {/* Control Panel */}
            <div>
                <button onClick={() => setIsStreaming(!isStreaming)}>
                    {isStreaming ? "Pause Logging" : "Resume Logging"}
                </button>
                <button onClick={fetchLogs}>Refresh Logs</button>
                <button onClick={fetchMetrics}>Refresh Metrics</button>
            </div>

            {/* Filters */}
            <div>
                <label>Search Logs:</label>
                <input
                    type="text"
                    value={filters.search}
                    onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                />
                <label>Severity:</label>
                <select
                    value={filters.severity}
                    onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
                >
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

            {/* Metrics Graph (Recharts) */}
            <div>
                <h3>System Metrics</h3>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={metrics}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="timestamp" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="cpuUsage" stroke="red" />
                        <Line type="monotone" dataKey="memoryUsage" stroke="blue" />
                        <Line type="monotone" dataKey="ioThroughput" stroke="green" />
                    </LineChart>
                </ResponsiveContainer>
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

// Dummy Export Function
const exportData = (format) => {
    console.log(`Exporting data as ${format}`);
};

export default HardwareLogsMetrics;
