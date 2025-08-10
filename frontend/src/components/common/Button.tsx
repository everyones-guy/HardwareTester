// src/components/common/Button.tsx
import React from "react";
import "./Button.css";

type Variant = "primary" | "secondary" | "danger" | "ghost";
type Size = "sm" | "md" | "lg";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: Variant;
    size?: Size;
}

const Button: React.FC<ButtonProps> = ({
    variant = "primary",
    size = "md",
    className = "",
    children,
    ...rest
}) => {
    const classes = [
        "btn",
        `btn-${variant}`,
        `btn-${size}`,
        className,
    ]
        .filter(Boolean)
        .join(" ");

    return (
        <button className={classes} {...rest}>
            {children}
        </button>
    );
};

export default Button;
