import React, { useEffect, useState } from "react";
import "./HardwareStats.css";

interface Stats {
    totalDevices: number;
    usbDevices: number;
    wifiDevices: number;
    bluetoothDevices: number;
    uptime: string;
    systemMemory: string;
}

const HardwareStats: React.FC = () => {
    const [stats, setStats] = useState<Stats | null>(null);

    useEffect(() => {
        const loadStats = async () => {
            try {
                const res = await fetch("/hardware/stats");
                const data = await res.json();
                setStats(data);
            } catch (err) {
                console.error("Failed to load hardware stats:", err);
            }
        };

        loadStats();
    }, []);

    return (
        <div className="hardware-stats">
            <h2>System Stats</h2>
            {stats ? (
                <ul>
                    <li><strong>Total Devices:</strong> {stats.totalDevices}</li>
                    <li><strong>USB:</strong> {stats.usbDevices}</li>
                    <li><strong>Wi-Fi:</strong> {stats.wifiDevices}</li>
                    <li><strong>Bluetooth:</strong> {stats.bluetoothDevices}</li>
                    <li><strong>Uptime:</strong> {stats.uptime}</li>
                    <li><strong>System Memory:</strong> {stats.systemMemory}</li>
                </ul>
            ) : (
                <p>Loading stats...</p>
            )}
        </div>
    );
};

export default HardwareStats;
