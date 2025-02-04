import React, { useEffect, useState } from "react";
import { listDevices, getDeviceDetails } from "../services/hardwareService";

const HardwarePanel = () => {
    const [devices, setDevices] = useState([]);
    const [selectedDevice, setSelectedDevice] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Fetch device list on mount
    useEffect(() => {
        fetchDevices();
    }, []);

    const fetchDevices = async () => {
        try {
            setLoading(true);
            const deviceList = await listDevices();
            setDevices(deviceList);
            setError(null);
        } catch (err) {
            console.error("Error fetching devices:", err);
            setError("Failed to load devices.");
        } finally {
            setLoading(false);
        }
    };

    const handleDeviceClick = async (deviceId) => {
        try {
            setLoading(true);
            const deviceDetails = await getDeviceDetails(deviceId);
            setSelectedDevice(deviceDetails);
            setError(null);
        } catch (err) {
            console.error("Error fetching device details:", err);
            setError("Failed to fetch device details.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="hardware-panel">
            <h3>Devices</h3>

            {error && <p className="error">{error}</p>}

            {loading ? (
                <p>Loading devices...</p>
            ) : (
                <ul>
                    {devices.length > 0 ? (
                        devices.map((device) => (
                            <li
                                key={device.id}
                                onClick={() => handleDeviceClick(device.id)}
                                style={{
                                    cursor: "pointer",
                                    fontWeight: selectedDevice?.id === device.id ? "bold" : "normal",
                                    background: selectedDevice?.id === device.id ? "#ddd" : "transparent",
                                    padding: "5px",
                                    borderRadius: "4px",
                                }}
                            >
                                {device.name}
                            </li>
                        ))
                    ) : (
                        <p>No devices found.</p>
                    )}
                </ul>
            )}

            {selectedDevice && (
                <div className="device-details">
                    <h4>Details for {selectedDevice.name}</h4>
                    <pre>{JSON.stringify(selectedDevice, null, 2)}</pre>
                </div>
            )}
        </div>
    );
};

export default HardwarePanel;
