import React, { useState, useEffect } from "react";
import "./PeripheralEditor.css";

interface Peripheral {
    id: string;
    name: string;
    type: string;
    address: string;
}

interface PeripheralEditorProps {
    peripheral: Peripheral;
    onSave: (updated: Peripheral) => void;
    onClose: () => void;
}

const PeripheralEditor: React.FC<PeripheralEditorProps> = ({ peripheral, onSave, onClose }) => {
    const [name, setName] = useState(peripheral.name);
    const [type, setType] = useState(peripheral.type);
    const [address, setAddress] = useState(peripheral.address);

    useEffect(() => {
        setName(peripheral.name);
        setType(peripheral.type);
        setAddress(peripheral.address);
    }, [peripheral]);

    const handleSave = () => {
        if (!name || !address) {
            alert("Name and Address are required.");
            return;
        }
        onSave({ ...peripheral, name, type, address });
        onClose();
    };

    return (
        <div className="peripheral-editor-overlay" onClick={onClose}>
            <div className="peripheral-editor-modal" onClick={(e) => e.stopPropagation()}>
                <h3>Edit Peripheral</h3>

                <input
                    type="text"
                    placeholder="Name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                />

                <select value={type} onChange={(e) => setType(e.target.value)}>
                    <option value="usb">USB</option>
                    <option value="wifi">Wi-Fi</option>
                    <option value="bluetooth">Bluetooth</option>
                    <option value="custom">Custom</option>
                </select>

                <input
                    type="text"
                    placeholder="Address or Port"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                />

                <div className="modal-actions">
                    <button onClick={handleSave}>Save</button>
                    <button onClick={onClose}>Cancel</button>
                </div>
            </div>
        </div>
    );
};

export default PeripheralEditor;
