import React from "react";
import HardwarePanel from "./HardwarePanel";
import EmulatorPanel from "./EmulatorPanel";
import MQTTPanel from "./MQTTPanel";
import SerialPanel from "./SerialPanel";

const Dashboard = () => {
    return (
        <div style={{ display: "flex", flexDirection: "row", height: "100vh" }}>
            <div style={{ flex: 1, padding: "10px", background: "#f5f5f5" }}>
                <HardwarePanel />
            </div>
            <div style={{ flex: 1, padding: "10px", background: "#e5e5e5" }}>
                <EmulatorPanel />
            </div>
            <div style={{ flex: 1, padding: "10px", background: "#d5d5d5" }}>
                <MQTTPanel />
            </div>
            <div style={{ flex: 1, padding: "10px", background: "#c5c5c5" }}>
                <SerialPanel />
            </div>
        </div>
    );
};

export default Dashboard;
