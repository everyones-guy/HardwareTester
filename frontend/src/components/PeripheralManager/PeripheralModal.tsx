import React from "react";
import "./PeripheralModal.css";

interface Peripheral {
    id: string;
    name: string;
    type: string;
    address: string;
    [key: string]: any;
}

interface PeripheralModalProps {
    peripheral: Peripheral;
    onClose: () => void;
}

const PeripheralModal: React.FC<PeripheralModalProps> = ({ peripheral, onClose }) => {
    return (
        <div className="peripheral-modal-overlay" onClick={onClose}>
            <div className="peripheral-modal" onClick={(e) => e.stopPropagation()}>
                <h3>Peripheral Details</h3>

                <ul className="peripheral-details">
                    {Object.entries(peripheral).map(([key, value]) => (
                        <li key={key}>
                            <strong>{key}:</strong> {String(value)}
                        </li>
                    ))}
                </ul>

                <div className="modal-actions">
                    <button onClick={onClose}>Close</button>
                </div>
            </div>
        </div>
    );
};

export default PeripheralModal;
