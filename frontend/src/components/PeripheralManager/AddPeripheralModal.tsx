import React, { useState } from "react";
import "./AddPeripheralModal.css";

interface AddPeripheralModalProps {
    onAdd: (data: { name: string; type: string; address: string }) => void;
    onClose: () => void;
}

const AddPeripheralModal: React.FC<AddPeripheralModalProps> = ({ onAdd, onClose }) => {
    const [name, setName] = useState("");
    const [type, setType] = useState("usb");
    const [address, setAddress] = useState("");

    const handleSubmit = () => {
        if (!name || !address) return alert("Name and Address are required.");
        onAdd({ name, type, address });
        onClose();
    };

    return (
        <div className="add-peripheral-overlay" onClick={onClose}>
            <div className="add-peripheral-modal" onClick={(e) => e.stopPropagation()}>
                <h3>Add Peripheral</h3>
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
                    <button onClick={handleSubmit}>Add</button>
                    <button onClick={onClose}>Cancel</button>
                </div>
            </div>
        </div>
    );
};

export default AddPeripheralModal;
