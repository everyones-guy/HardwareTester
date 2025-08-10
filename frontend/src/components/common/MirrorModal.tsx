import React from "react";

interface MirrorModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: (makeStandalone: boolean) => void;
    hardwareName: string;
}

const MirrorModal: React.FC<MirrorModalProps> = ({ isOpen, onClose, onConfirm, hardwareName }) => {
    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <h3>Mirror Hardware: {hardwareName}</h3>
                <p>
                    Would you like to mirror this hardware setup? You can also choose to make the
                    mirrored version a standalone copy for replication or testing.
                </p>

                <div className="modal-actions">
                    <button onClick={() => onConfirm(false)}>Mirror Only</button>
                    <button onClick={() => onConfirm(true)}>Mirror as Standalone</button>
                    <button onClick={onClose} className="cancel-button">
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    );
};

export default MirrorModal;
