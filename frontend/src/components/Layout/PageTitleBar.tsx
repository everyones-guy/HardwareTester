import React from "react";
import "./PageTitleBar.css";

interface PageTitleBarProps {
    title: string;
    subtitle?: string;
    actions?: React.ReactNode;
}

const PageTitleBar: React.FC<PageTitleBarProps> = ({ title, subtitle, actions }) => {
    return (
        <div className="page-title-bar">
            <div className="title-content">
                <h2 className="page-title">{title}</h2>
                {subtitle && <p className="page-subtitle">{subtitle}</p>}
            </div>
            {actions && <div className="title-actions">{actions}</div>}
        </div>
    );
};

export default PageTitleBar;
