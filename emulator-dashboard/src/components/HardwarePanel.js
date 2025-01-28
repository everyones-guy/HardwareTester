import React, { useEffect, useState } from "react";
import { listDevices, getDeviceDetails } from "../services/hardwareService";

const HardwarePanel = () => {
    const [devices, setDevices] = useState([]);
    const [selectedDevice, setSelectedDevice] = useState(null);

    useEffect(() => {
        listDevices().then(setDevices);
    }, []);

    const handleDeviceClick = (deviceId) => {
        getDeviceDetails(deviceId).then(setSelectedDevice);
    };

    return (
        <div>
            <h3>Devices</h3>
            <ul>
                {devices.map((device) => (
                    <li key={device.id} onClick={() => handleDeviceClick(device.id)}>
                        {device.name}
                    </li>
                ))}
            </ul>
            {selectedDevice && (
                <div>
                    <h4>Details for {selectedDevice.name}</h4>
                    <pre>{JSON.stringify(selectedDevice, null, 2)}</pre>
                </div>
            )}
        </div>
    );
};

export default HardwarePanel;
