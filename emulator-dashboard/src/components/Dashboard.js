import React from "react";
import HardwarePanel from "./HardwarePanel";
import EmulatorPanel from "./EmulatorPanel";
import MQTTPanel from "./MQTTPanel";
import SerialPanel from "./SerialPanel";
import LiveMetrics from "./LiveMetrics";
import MirrorModal from "./MirrorModal";
import ActiveEmulations from "./ActiveEmulations";


const Dashboard = () => {
    return (
        <div style={{ display: "flex", flexDirection: "row", height: "100vh" }}>
            <div style={{ flex: 1, padding: "10px", background: "#f5f5f5" }}>
                <h1>Hardware Emulator Dashboard</h1>
                <HardwarePanel />
            </div>
            <div style={{ flex: 1, padding: "10px", background: "#e5e5e5" }}>
                <h1>Hardware Emulator Dashboard</h1>
                <EmulatorPanel />
            </div>
            <div style={{ flex: 1, padding: "10px", background: "#d5d5d5" }}>
                <h1>Hardware Emulator Dashboard</h1>
                <MQTTPanel />
            </div>
            <div style={{ flex: 1, padding: "10px", background: "#c5c5c5" }}>
                <h1>Hardware Emulator Dashboard</h1>
                <SerialPanel />
            </div> 
            <div style={{ flex: 1, padding: "10px", background: "#c5c5c5" }}>
                <h1>Hardware Emulator Dashboard</h1>
                <LiveMetrics />
            </div>
            <div style={{ flex: 1, padding: "10px", background: "#c5c5c5" }}>
                <h1>Hardware Emulator Dashboard</h1>
                <MirrorModal />
            </div>
        </div>
    );
};

export default Dashboard;
