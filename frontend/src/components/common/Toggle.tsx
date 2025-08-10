import React from "react";
import "./Toggle.css";

interface ToggleProps {
    label?: string;
    checked: boolean;
    onChange: (checked: boolean) => void;
    disabled?: boolean;
    labelPosition?: "left" | "right";
}

const Toggle: React.FC<ToggleProps> = ({
    label,
    checked,
    onChange,
    disabled = false,
    labelPosition = "right",
}) => {
    return (
        <div className="toggle-container">
            {label && labelPosition === "left" && (
                <label className="toggle-label">{label}</label>
            )}

            <label className="toggle-switch">
                <input
                    type="checkbox"
                    checked={checked}
                    onChange={(e) => onChange(e.target.checked)}
                    disabled={disabled}
                />
                <span className="slider" />
            </label>

            {label && labelPosition === "right" && (
                <label className="toggle-label">{label}</label>
            )}
        </div>
    );
};

export default Toggle;
