// src/components/ConnectionDashboard/ConnectionDashboard.tsx
import React from "react";
import MQTTPanel from "./MQTTPanel";
import USBPanel from "./USBPanel";
import SerialPanel from "./SerialPanel";
import BluetoothPanel from "./BluetoothPanel";
import "./ConnectionDashboard.css";
import "@/components/common/dashboard.css";

const ConnectionDashboard: React.FC = () => {
    return (
        <div className="connection-dashboard">
            <div className="dashboard-header">
                <h1>Connections</h1>
            </div>

            <div className="connection-sections">
                <section className="connection-section"><MQTTPanel /></section>
                <section className="connection-section"><SerialPanel /></section>
                <section className="connection-section"><USBPanel /></section>
                <section className="connection-section"><BluetoothPanel /></section>
            </div>
        </div>
    );
};

export default ConnectionDashboard;
