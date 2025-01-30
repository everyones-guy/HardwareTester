import React, { useState, useEffect, useRef, useCallback } from "react";
import { connectMQTT, listenToMQTT, unsubscribeFromTopic } from "../services/mqttService";
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

    // Chart references
    const cpuChartRef = useRef(null);
    const memoryChartRef = useRef(null);
    const networkChartRef = useRef(null);

    /**
     * Handles incoming system metrics (CPU, Memory, Network).
     */
    const handleMetricUpdate = useCallback((type, message) => {
        const value = parseFloat(message);
        switch (type) {
            case "cpu":
                setCpuData((prev) => [...prev.slice(-49), value]);
                checkThreshold("CPU", value, 85);
                break;
            case "memory":
                setMemoryData((prev) => [...prev.slice(-49), value]);
                checkThreshold("Memory", value, 90);
                break;
            case "network":
                setNetworkData((prev) => [...prev.slice(-49), value]);
                break;
            case "devices":
                const data = JSON.parse(message);
                setDeviceMetrics((prevMetrics) => ({ ...prevMetrics, ...data }));
                break;
            default:
                console.warn("Unknown metric type:", type);
        }
    }, []);

    /**
     * Initializes charts when the component mounts.
     */
    const initializeCharts = useCallback(() => {
        const ctxCPU = document.getElementById("cpuChart").getContext("2d");
        const ctxMemory = document.getElementById("memoryChart").getContext("2d");
        const ctxNetwork = document.getElementById("networkChart").getContext("2d");

        cpuChartRef.current = createChart(ctxCPU, "CPU Usage");
        memoryChartRef.current = createChart(ctxMemory, "Memory Usage");
        networkChartRef.current = createChart(ctxNetwork, "Network Traffic");
    }, []);

    useEffect(() => {
        connectMQTT();
        fetchSystemMetrics();
        fetchActiveEmulations();
        initializeCharts();

        const topics = {
            cpu: "system/cpu",
            memory: "system/memory",
            network: "system/network",
            devices: "devices/metrics",
        };

        Object.entries(topics).forEach(([type, topic]) => {
            listenToMQTT(topic, (message) => handleMetricUpdate(type, message));
        });

        return () => {
            Object.values(topics).forEach((topic) => unsubscribeFromTopic(topic));

            if (cpuChartRef.current) cpuChartRef.current.destroy();
            if (memoryChartRef.current) memoryChartRef.current.destroy();
            if (networkChartRef.current) networkChartRef.current.destroy();
        };
    }, [handleMetricUpdate, initializeCharts]);

    const fetchSystemMetrics = async () => {
        try {
            const status = await getSystemStatus();
            setSystemStatus(status);
        } catch (error) {
            console.error("Error fetching system metrics:", error);
        }
    };

    const fetchActiveEmulations = async () => {
        try {
            const emulations = await getActiveEmulations();
            setActiveEmulations(emulations);
        } catch (error) {
            console.error("Error fetching active emulations:", error);
        }
    };

    const checkThreshold = (metric, value, threshold) => {
        if (value > threshold) {
            setAlerts((prevAlerts) => [
                ...prevAlerts.slice(-4),
                `${metric} Usage HIGH: ${value}% (Threshold: ${threshold}%)`,
            ]);
        }
    };

    const createChart = (ctx, label) => {
        return new Chart(ctx, {
            type: "line",
            data: {
                labels: Array(50).fill(""),
                datasets: [
                    {
                        label: label,
                        data: [],
                        borderColor: "rgba(75,192,192,1)",
                        fill: false,
                    },
                ],
            },
            options: {
                responsive: true,
                scales: {
                    x: { display: false },
                    y: { beginAtZero: true },
                },
            },
        });
    };

    return (
        <div className="live-metrics">
            <h1>Live System Metrics</h1>

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

            <h2>Active Emulations</h2>
            <ul>
                {activeEmulations.map((emu) => (
                    <li key={emu.id}>
                        {emu.name} - {emu.status}
                    </li>
                ))}
            </ul>

            <h2>Device Telemetry</h2>
            <ul>
                {Object.entries(deviceMetrics).map(([key, value]) => (
                    <li key={key}>
                        {key}: {value}
                    </li>
                ))}
            </ul>

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
