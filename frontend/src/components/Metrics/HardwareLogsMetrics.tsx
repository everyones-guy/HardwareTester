import React, { useEffect, useState } from "react";
import "./HardwareLogsMetrics.css";

interface HardwareLog {
    timestamp: string;
    message: string;
    type: "info" | "warning" | "error";
}

interface HardwareStats {
    total: number;
    usb: number;
    wifi: number;
    bluetooth: number;
    uptime: string;
}

const HardwareLogsMetrics: React.FC = () => {
    const [logs, setLogs] = useState<HardwareLog[]>([]);
    const [stats, setStats] = useState<HardwareStats | null>(null);

    useEffect(() => {
        fetchLogs();
        fetchStats();
    }, []);

    const fetchLogs = async () => {
        try {
            const res = await fetch("/hardware/logs");
            const data = await res.json();
            setLogs(data);
        } catch (err) {
            console.error("Failed to fetch logs:", err);
        }
    };

    const fetchStats = async () => {
        try {
            const res = await fetch("/hardware/stats");
            const data = await res.json();
            setStats(data);
        } catch (err) {
            console.error("Failed to fetch stats:", err);
        }
    };

    return (
        <div className="hardware-logs-metrics">
            <div className="metrics-panel">
                <h3>Device Stats</h3>
                {stats ? (
                    <ul>
                        <li><strong>Total:</strong> {stats.total}</li>
                        <li><strong>USB:</strong> {stats.usb}</li>
                        <li><strong>Wi-Fi:</strong> {stats.wifi}</li>
                        <li><strong>Bluetooth:</strong> {stats.bluetooth}</li>
                        <li><strong>Uptime:</strong> {stats.uptime}</li>
                    </ul>
                ) : (
                    <p>Loading stats...</p>
                )}
            </div>

            <div className="logs-panel">
                <h3>Recent Events</h3>
                <ul className="log-list">
                    {logs.length > 0 ? (
                        logs.slice(-50).reverse().map((log, idx) => (
                            <li key={idx} className={`log-item ${log.type}`}>
                                <span className="log-time">[{log.timestamp}]</span> {log.message}
                            </li>
                        ))
                    ) : (
                        <p>No logs available.</p>
                    )}
                </ul>
            </div>
        </div>
    );
};

export default HardwareLogsMetrics;
