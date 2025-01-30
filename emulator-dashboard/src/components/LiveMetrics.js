import React, { useState, useEffect } from "react";
import { connectMQTT, listenToMQTT } from "../services/mqttService";
import { getSystemStatus, getActiveEmulations } from "../services/dashboardService";
import Chart from "chart.js/auto";

const LiveMetrics = () => {
    const [systemStatus, setSystemStatus] = useState({});
    const [activeEmulations, setActiveEmulations] = useState([]);
    const [cpuData, setCpuData] = useState([]);
    const [memoryData, setMemoryData] = useState([]);
    const [networkData, setNetworkData] = useState([]);
    const [deviceMetrics, setDeviceMetrics] = useState({});
    const [alerts, setAlerts] = useState([]);

    let cpuChart, memoryChart, networkChart;

    useEffect(() => {
        connectMQTT();

        // Fetch Initial Data
        fetchSystemMetrics();
        fetchActiveEmulations();

        // Listen for Live Hardware Metrics from MQTT
        listenToMQTT("system/cpu", (message) => handleMetricUpdate("cpu", message));
        listenToMQTT("system/memory", (message) => handleMetricUpdate("memory", message));
        listenToMQTT("system/network", (message) => handleMetricUpdate("network", message));
        listenToMQTT("devices/metrics", (message) => handleDeviceMetrics(message));
        listenToMQTT("device/metrics", (message) => {
            console.log("Live Metrics:", message);
        });

        return () => {
            if (cpuChart) cpuChart.destroy();
            if (memoryChart) memoryChart.destroy();
            if (networkChart) networkChart.destroy();
        };
    }, []);

    /**
     * Fetch system health metrics from backend API.
     */
    const fetchSystemMetrics = async () => {
        try {
            const status = await getSystemStatus();
            setSystemStatus(status);
        } catch (error) {
            console.error("Error fetching system metrics:", error);
        }
    };

    /**
     * Fetch active emulations from backend API.
     */
    const fetchActiveEmulations = async () => {
        try {
            const emulations = await getActiveEmulations();
            setActiveEmulations(emulations);
        } catch (error) {
            console.error("Error fetching active emulations:", error);
        }
    };

    /**
     * Handles incoming system metrics (CPU, Memory, Network).
     */
    const handleMetricUpdate = (type, message) => {
        const value = parseFloat(message);
        switch (type) {
            case "cpu":
                updateChart(cpuData, setCpuData, value);
                checkThreshold("CPU", value, 85);
                break;
            case "memory":
                updateChart(memoryData, setMemoryData, value);
                checkThreshold("Memory", value, 90);
                break;
            case "network":
                updateChart(networkData, setNetworkData, value);
                break;
            default:
                console.warn("Unknown metric type:", type);
        }
    };

    /**
     * Handles incoming device telemetry data.
     */
    const handleDeviceMetrics = (message) => {
        const data = JSON.parse(message);
        setDeviceMetrics((prevMetrics) => ({ ...prevMetrics, ...data }));
    };

    /**
     * Updates chart data dynamically.
     */
    const updateChart = (dataArray, setDataArray, newValue) => {
        const updatedData = [...dataArray, newValue];
        if (updatedData.length > 50) updatedData.shift(); // Keep only latest 50 values
        setDataArray(updatedData);
    };

    /**
     * Checks if a metric has exceeded a threshold and triggers an alert.
     */
    const checkThreshold = (metric, value, threshold) => {
        if (value > threshold) {
            setAlerts((prevAlerts) => [
                ...prevAlerts,
                `${metric} Usage HIGH: ${value}% (Threshold: ${threshold}%)`,
            ]);
        }
    };

    return (
        <div className="live-metrics">
            <h1>Live System Metrics</h1>

            {/* System Status */}
            <div className="metrics-container">
                <div className="metric-box">
                    <h2>CPU Usage</h2>
                    <p>{systemStatus.cpu}%</p>
                    <canvas id="cpuChart"></canvas>
                </div>
                <div className="metric-box">
                    <h2>Memory Usage</h2>
                    <p>{systemStatus.memory}%</p>
                    <canvas id="memoryChart"></canvas>
                </div>
                <div className="metric-box">
                    <h2>Network Traffic</h2>
                    <p>{systemStatus.network} Mbps</p>
                    <canvas id="networkChart"></canvas>
                </div>
            </div>

            {/* Active Emulations */}
            <h2>Active Emulations</h2>
            <ul>
                {activeEmulations.map((emu) => (
                    <li key={emu.id}>
                        {emu.name} - {emu.status}
                    </li>
                ))}
            </ul>

            {/* Live Device Metrics */}
            <h2>Device Telemetry</h2>
            <ul>
                {Object.entries(deviceMetrics).map(([key, value]) => (
                    <li key={key}>
                        {key}: {value}
                    </li>
                ))}
            </ul>

            {/* Alerts Section */}
            {alerts.length > 0 && (
                <div className="alerts">
                    <h2>Alerts</h2>
                    <ul>
                        {alerts.map((alert, index) => (
                            <li key={index}>{alert}</li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
};

export default LiveMetrics;
