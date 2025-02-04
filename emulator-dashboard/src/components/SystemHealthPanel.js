import React, { useState, useEffect } from "react";
import { getSystemStatus, subscribeToSystemHealth } from "../services/dashboardService";

const SystemHealthPanel = () => {
    const [systemStatus, setSystemStatus] = useState({
        cpu: "Loading...",
        memory: "Loading...",
        network: "Loading...",
    });

    useEffect(() => {
        fetchSystemHealth();

        // Subscribe to real-time system updates
        const unsubscribe = subscribeToSystemHealth((data) => setSystemStatus(data));

        return () => unsubscribe(); // Cleanup WebSocket on component unmount
    }, []);

    const fetchSystemHealth = async () => {
        const data = await getSystemStatus();
        setSystemStatus(data);
    };

    return (
        <div className="system-health-panel">
            <h2>System Health</h2>
            <button onClick={fetchSystemHealth}>Refresh</button>
            <p><strong>CPU Usage:</strong> {systemStatus.cpu}%</p>
            <p><strong>Memory Usage:</strong> {systemStatus.memory}%</p>
            <p><strong>Network Usage:</strong> {systemStatus.network} Mbps</p>
        </div>
    );
};

export default SystemHealthPanel;
