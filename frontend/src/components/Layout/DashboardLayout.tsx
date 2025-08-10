// src/components/Layout/DashboardLayout.tsx
import React from "react";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import "./DashboardLayout.css"; // optional for layout styling
import "../../index.css"; // for shared styles

const DashboardLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    return (
        <div className="dashboard-layout">
            <Sidebar />
            <div className="main-content">
                <Topbar />
                <div className="content-area">
                    {children}
                </div>
            </div>
        </div>
    );
};

export default DashboardLayout;
