// src/components/common/Card.tsx
import React from "react";
import "./Card.css";

interface CardProps {
    children: React.ReactNode;
    className?: string;
}

const Card: React.FC<CardProps> = ({ children, className = "" }) => {
    return <div className={`common-card ${className}`}>{children}</div>;
};

export const CardContent: React.FC<CardProps> = ({ children, className = "" }) => {
    return <div className={`common-card-content ${className}`}>{children}</div>;
};

export default Card;
