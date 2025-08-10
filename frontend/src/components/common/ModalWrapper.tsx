import React from "react";
import "./ModalWrapper.css";

interface ModalWrapperProps {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    children: React.ReactNode;
    width?: string;
}

const ModalWrapper: React.FC<ModalWrapperProps> = ({
    isOpen,
    onClose,
    title,
    children,
    width = "500px",
}) => {
    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div
                className="modal-container"
                style={{ width }}
                onClick={(e) => e.stopPropagation()}
            >
                {title && <h2 className="modal-title">{title}</h2>}
                <div className="modal-body">{children}</div>
                <div className="modal-footer">
                    <button className="modal-close-button" onClick={onClose}>
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ModalWrapper;
