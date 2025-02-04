import React, { useState, useEffect, useCallback } from "react";
import { Client } from "paho-mqtt";
import { getSystemStatus, getActiveEmulations } from "../services/dashboardService";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

const MQTT_BROKER = "wss://broker.hivemq.com/mqtt"; // Change this if using a private broker.
const CLIENT_ID = `mqtt_client_${Math.random().toString(16).substr(2, 8)}`;

const LiveMetrics = () => {
    const [systemStatus, setSystemStatus] = useState({});
    const [activeEmulations, setActiveEmulations] = useState([]);
    const [cpuData, setCpuData] = useState([]);
    const [memoryData, setMemoryData] = useState([]);
    const [networkData, setNetworkData] = useState([]);
    const [deviceMetrics, setDeviceMetrics] = useState({});
    const [alerts, setAlerts] = useState([]);
    const [mqttClient, setMqttClient] = useState(null);

    // Handle MQTT Messages
    const handleMetricUpdate = useCallback((type, message) => {
        const value = parseFloat(message);
        switch (type) {
            case "cpu":
                setCpuData((prev) => [...prev.slice(-49), { timestamp: new Date().toLocaleTimeString(), value }]);
                checkThreshold("CPU", value, 85);
                break;
            case "memory":
                setMemoryData((prev) => [...prev.slice(-49), { timestamp: new Date().toLocaleTimeString(), value }]);
                checkThreshold("Memory", value, 90);
                break;
            case "network":
                setNetworkData((prev) => [...prev.slice(-49), { timestamp: new Date().toLocaleTimeString(), value }]);
                break;
            case "devices":
                const data = JSON.parse(message);
                setDeviceMetrics((prevMetrics) => ({ ...prevMetrics, ...data }));
                break;
            default:
                console.warn("Unknown metric type:", type);
        }
    }, []);

    // Initialize MQTT Connection
    useEffect(() => {
        const client = new Client(MQTT_BROKER, CLIENT_ID);
        setMqttClient(client);

        client.connect({
            onSuccess: () => {
                console.log("Connected to MQTT broker");
                client.subscribe("system/cpu");
                client.subscribe("system/memory");
                client.subscribe("system/network");
                client.subscribe("devices/metrics");

                client.onMessageArrived = (message) => {
                    const topic = message.destinationName;
                    const payload = message.payloadString;
                    if (topic.includes("cpu")) handleMetricUpdate("cpu", payload);
                    if (topic.includes("memory")) handleMetricUpdate("memory", payload);
                    if (topic.includes("network")) handleMetricUpdate("network", payload);
                    if (topic.includes("devices")) handleMetricUpdate("devices", payload);
                };
            },
            onFailure: (error) => {
                console.error("MQTT Connection Failed:", error);
            }
        });

        return () => {
            client.disconnect();
            console.log("Disconnected from MQTT broker");
        };
    }, [handleMetricUpdate]);

    // Fetch initial system metrics
    useEffect(() => {
        fetchSystemMetrics();
        fetchActiveEmulations();
    }, []);

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

    return (
        <div className="live-metrics">
            <h1>Live System Metrics</h1>

            <div className="metrics-container">
                {/* CPU Chart */}
                <div className="metric-box">
                    <h2>CPU Usage</h2>
                    <p>{systemStatus.cpu}%</p>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={cpuData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="timestamp" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Line type="monotone" dataKey="value" stroke="red" />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* Memory Chart */}
                <div className="metric-box">
                    <h2>Memory Usage</h2>
                    <p>{systemStatus.memory}%</p>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={memoryData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="timestamp" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Line type="monotone" dataKey="value" stroke="blue" />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* Network Chart */}
                <div className="metric-box">
                    <h2>Network Traffic</h2>
                    <p>{systemStatus.network} Mbps</p>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={networkData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="timestamp" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Line type="monotone" dataKey="value" stroke="green" />
                        </LineChart>
                    </ResponsiveContainer>
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

            {/* Device Telemetry */}
            <h2>Device Telemetry</h2>
            <ul>
                {Object.entries(deviceMetrics).map(([key, value]) => (
                    <li key={key}>
                        {key}: {value}
                    </li>
                ))}
            </ul>

            {/* Alerts */}
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
