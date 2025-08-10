// src/components/HardwareDashboard/HardwarePanel.tsx
import React, { useEffect, useMemo, useState } from "react";
import HardwareService from "@/services/hardwareService";
import { FaUsb, FaWifi, FaBluetooth } from "react-icons/fa";
import DeviceModal from "./DeviceModal";
import "./HardwarePanel.css";
// If you have device types, import them:
// import { Device } from "@/types/hardwareTypes";

type HardwareDevice = {
    id: string;
    name: string;
    type: "usb" | "wifi" | "bluetooth" | string;
    status?: string;
    [key: string]: any;
};

const iconForType = (t?: string) => {
    switch ((t || "").toLowerCase()) {
        case "usb":
            return <FaUsb title="USB" />;
        case "wifi":
        case "wi-fi":
            return <FaWifi title="Wi-Fi" />;
        case "bluetooth":
            return <FaBluetooth title="Bluetooth" />;
        default:
            return null;
    }
};

const HardwarePanel: React.FC = () => {
    const [devices, setDevices] = useState<HardwareDevice[]>([]);
    const [selectedDevice, setSelectedDevice] = useState<HardwareDevice | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [filterType, setFilterType] = useState<string>("all");

    const loadDevices = async () => {
        setLoading(true);
        setError(null);
        try {
            // Unwrap defensively in case your service returns {success, data:{devices}} or similar
            const res = await HardwareService.listDevices();
            const list: HardwareDevice[] =
                // @ts-ignore tolerate various envelopes
                res?.data?.devices ?? res?.devices ?? res ?? [];
            setDevices(Array.isArray(list) ? list : []);
        } catch (e: any) {
            console.error("Error fetching devices:", e);
            setError(e?.message || "Failed to load devices.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadDevices();
    }, []);

    const handleDeviceClick = async (deviceId: string) => {
        setLoading(true);
        setError(null);
        try {
            const res = await HardwareService.getDeviceDetails(deviceId);
            const details: HardwareDevice =
                // @ts-ignore unwrap common shapes
                res?.data?.device ?? res?.device ?? res;
            setSelectedDevice(details);
        } catch (e: any) {
            console.error("Error fetching device details:", e);
            setError(e?.message || "Failed to fetch device details.");
        } finally {
            setLoading(false);
        }
    };

    // Build filter options from actual devices
    const typeOptions = useMemo(() => {
        const set = new Set<string>();
        devices.forEach((d) => d.type && set.add(d.type.toLowerCase()));
        return ["all", ...Array.from(set).sort()];
    }, [devices]);

    const filteredDevices = useMemo(() => {
        const ft = filterType.toLowerCase();
        return devices.filter((d) =>
            ft === "all" ? true : (d.type || "").toLowerCase() === ft
        );
    }, [devices, filterType]);

    return (
        <div className="hardware-panel">
            <div className="panel-header">
                <h2>Connected Devices</h2>
                <div className="controls" style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                    <label htmlFor="type-filter">Filter:</label>
                    <select
                        id="type-filter"
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                    >
                        {typeOptions.map((t) => (
                            <option key={t} value={t}>
                                {t === "all" ? "All Types" : t.toUpperCase()}
                            </option>
                        ))}
                    </select>
                    <button onClick={loadDevices} disabled={loading}>
                        {loading ? "Refreshing..." : "Refresh"}
                    </button>
                    <span style={{ opacity: 0.7 }}>
                        {filteredDevices.length}/{devices.length}
                    </span>
                </div>
            </div>

            {error && <div className="error">{error}</div>}

            {loading && devices.length === 0 ? (
                <p>Loading devices...</p>
            ) : filteredDevices.length === 0 ? (
                <p>No devices found.</p>
            ) : (
                <ul className="device-list">
                    {filteredDevices.map((device) => (
                        <li
                            key={device.id}
                            className={`device-item ${selectedDevice?.id === device.id ? "selected" : ""
                                }`}
                            onClick={() => handleDeviceClick(device.id)}
                        >
                            <span className="device-icon">{iconForType(device.type)}</span>
                            <div className="device-meta">
                                <span className="device-name">{device.name}</span>
                                {device.status && (
                                    <span className={`device-status status-${device.status.toLowerCase()}`}>
                                        {device.status}
                                    </span>
                                )}
                            </div>
                        </li>
                    ))}
                </ul>
            )}

            {selectedDevice && (
                <DeviceModal device={selectedDevice} onClose={() => setSelectedDevice(null)} />
            )}
        </div>
    );
};

export default HardwarePanel;
