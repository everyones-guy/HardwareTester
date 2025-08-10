import React from "react";
import "./DeviceModal.css";

interface DeviceModalProps {
    device: Record<string, any>;
    onClose: () => void;
}

const DeviceModal: React.FC<DeviceModalProps> = ({ device, onClose }) => {
    return (
        <div className="device-modal-overlay" onClick={onClose}>
            <div className="device-modal" onClick={(e) => e.stopPropagation()}>
                <h3>{device.name}</h3>
                <pre>{JSON.stringify(device, null, 2)}</pre>
                <button onClick={onClose}>Close</button>
            </div>
        </div>
    );
};

export default DeviceModal;
