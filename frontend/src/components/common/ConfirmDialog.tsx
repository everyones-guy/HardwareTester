import React from "react";

interface ConfirmDialogProps {
    title?: string;
    message: string;
    onConfirm: () => void;
    onCancel: () => void;
    confirmText?: string;
    cancelText?: string;
    isOpen?: boolean;
    open?: boolean;
    disableConfirm?: boolean;
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
    title = "Are you sure?",
    message,
    onConfirm,
    onCancel,
    confirmText = "Yes",
    cancelText = "Cancel",
    isOpen,
    open,
    disableConfirm,
}) => {
    if (!(isOpen ?? open)) return null;

    return (
        <div className="confirm-dialog-overlay">
            <div className="confirm-dialog-box">
                <h3>{title}</h3>
                <p>{message}</p>
                <div className="confirm-dialog-actions">
                    <button className="btn btn-secondary" onClick={onCancel}>
                        {cancelText}
                    </button>
                    <button className="btn btn-primary" disabled={disableConfirm} onClick={onConfirm}>
                        {confirmText}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ConfirmDialog;
