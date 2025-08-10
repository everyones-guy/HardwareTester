// src/components/ConnectionDashboard/BluetoothPanel.tsx
import React, { useEffect, useState } from "react";
import APIService from "@/services/apiService";
import "./BluetoothPanel.css";

interface BluetoothDevice {
    name: string;
    address: string;
    rssi?: number;
}

const BluetoothPanel: React.FC = () => {
    const [devices, setDevices] = useState<BluetoothDevice[]>([]);
    const [selectedDevice, setSelectedDevice] = useState<string>("");
    const [isConnected, setIsConnected] = useState(false);
    const [log, setLog] = useState<string[]>([]);
    const [autoReconnect, setAutoReconnect] = useState(true);

    const logMessage = (msg: string) => {
        setLog((prev) => [...prev.slice(-49), msg]);
    };

    const scanForDevices = async () => {
        try {
            const res = await APIService.apiCallWithRetry<any>("bluetooth/scan", "GET");
            const list: BluetoothDevice[] = Array.isArray(res?.devices)
                ? res.devices
                : Array.isArray(res)
                    ? res
                    : [];
            setDevices(list);
            logMessage("Scan complete.");
        } catch (error: any) {
            logMessage("Scan error: " + (error?.message || "Unknown error"));
        }
    };

    const handleConnect = async () => {
        if (!selectedDevice) {
            alert("Select a device to connect.");
            return;
        }
        try {
            await APIService.apiCallWithRetry("bluetooth/connect", "POST", {
                address: selectedDevice,
                autoReconnect,
            });
            setIsConnected(true);
            logMessage("Connected to device.");
        } catch (error: any) {
            logMessage("Connection error: " + (error?.message || "Unknown error"));
        }
    };

    const handleDisconnect = async () => {
        try {
            await APIService.apiCallWithRetry("bluetooth/disconnect", "POST");
            setIsConnected(false);
            logMessage("Disconnected.");
        } catch (error: any) {
            logMessage("Disconnection error: " + (error?.message || "Unknown error"));
        }
    };

    useEffect(() => {
        // Optional auto-scan on mount
        scanForDevices();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <div className="bluetooth-panel">
            <div className="bt-controls">
                <button onClick={scanForDevices}>Scan for Devices</button>

                <select
                    value={selectedDevice}
                    onChange={(e) => setSelectedDevice(e.target.value)}
                    disabled={isConnected}
                >
                    <option value="">-- Select a device --</option>
                    {devices.map((dev, index) => (
                        <option key={index} value={dev.address}>
                            {dev.name || "Unnamed Device"} ({dev.address})
                        </option>
                    ))}
                </select>

                {!isConnected ? (
                    <button onClick={handleConnect} disabled={!selectedDevice}>
                        Connect
                    </button>
                ) : (
                    <button onClick={handleDisconnect}>Disconnect</button>
                )}

                <label className="bt-toggle">
                    <input
                        type="checkbox"
                        checked={autoReconnect}
                        onChange={() => setAutoReconnect(!autoReconnect)}
                        disabled={isConnected} /* avoid toggling while connected */
                    />
                    Auto Reconnect
                </label>
            </div>

            <div className="bt-log">
                <h4>Log</h4>
                <textarea value={log.join("\n")} readOnly rows={10} />
            </div>
        </div>
    );
};

export default BluetoothPanel;
