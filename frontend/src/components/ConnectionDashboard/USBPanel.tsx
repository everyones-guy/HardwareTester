// src/components/ConnectionDashboard/USBPanel.tsx
import React, { useEffect, useState } from "react";
import APIService from "@/services/apiService";
import "./USBPanel.css";

interface USBDeviceInfo {
    id: string;
    name: string;
    vendorId?: string;
    productId?: string;
    serialNumber?: string;
}

const USBPanel: React.FC = () => {
    const [devices, setDevices] = useState<USBDeviceInfo[]>([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState<string>("");
    const [isConnected, setIsConnected] = useState(false);
    const [log, setLog] = useState<string[]>([]);

    const logMessage = (msg: string) => setLog((prev) => [...prev.slice(-49), msg]);

    const fetchDevices = async () => {
        try {
            const res = await APIService.apiCallWithRetry<any>("usb/devices", "GET");
            const list: USBDeviceInfo[] = Array.isArray(res?.devices)
                ? res.devices
                : Array.isArray(res)
                    ? res
                    : [];
            setDevices(list);
            logMessage("USB devices refreshed.");
        } catch (error: any) {
            logMessage("Fetch error: " + (error?.message || "Unknown error"));
        }
    };

    const handleConnect = async () => {
        if (!selectedDeviceId) return;
        try {
            await APIService.apiCallWithRetry("usb/connect", "POST", { id: selectedDeviceId });
            setIsConnected(true);
            logMessage("Connected to USB device.");
        } catch (error: any) {
            logMessage("Connect error: " + (error?.message || "Unknown error"));
        }
    };

    const handleDisconnect = async () => {
        try {
            await APIService.apiCallWithRetry("usb/disconnect", "POST");
            setIsConnected(false);
            logMessage("Disconnected.");
        } catch (error: any) {
            logMessage("Disconnect error: " + (error?.message || "Unknown error"));
        }
    };

    useEffect(() => {
        fetchDevices();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const selectedDevice = devices.find((d) => d.id === selectedDeviceId);

    return (
        <div className="usb-panel">
            <h2>USB Device Panel</h2>

            <div className="usb-controls">
                <button onClick={fetchDevices}>Refresh Devices</button>

                <select
                    value={selectedDeviceId}
                    onChange={(e) => setSelectedDeviceId(e.target.value)}
                    disabled={isConnected}
                >
                    <option value="">-- Select a device --</option>
                    {devices.map((device) => (
                        <option key={device.id} value={device.id}>
                            {device.name || "Unnamed Device"} ({device.id})
                        </option>
                    ))}
                </select>

                {!isConnected ? (
                    <button onClick={handleConnect} disabled={!selectedDeviceId}>
                        Connect
                    </button>
                ) : (
                    <button onClick={handleDisconnect}>Disconnect</button>
                )}
            </div>

            {selectedDevice && (
                <div className="usb-info">
                    <h4>Device Info</h4>
                    <ul>
                        <li>
                            <strong>Name:</strong> {selectedDevice.name}
                        </li>
                        <li>
                            <strong>Vendor ID:</strong> {selectedDevice.vendorId || "N/A"}
                        </li>
                        <li>
                            <strong>Product ID:</strong> {selectedDevice.productId || "N/A"}
                        </li>
                        <li>
                            <strong>Serial:</strong> {selectedDevice.serialNumber || "N/A"}
                        </li>
                    </ul>
                </div>
            )}

            <div className="usb-log">
                <h4>Log</h4>
                <textarea value={log.join("\n")} readOnly rows={10} />
            </div>
        </div>
    );
};

export default USBPanel;
