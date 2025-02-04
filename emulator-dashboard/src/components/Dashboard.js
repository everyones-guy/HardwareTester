import React from "react";
import HardwarePanel from "./HardwarePanel";
import EmulatorPanel from "./EmulatorPanel";
import MQTTPanel from "./MQTTPanel";
import SerialPanel from "./SerialPanel";
import LiveMetrics from "./LiveMetrics";
import MirrorModal from "./MirrorModal";
import ActiveEmulations from "./ActiveEmulations";
import SystemHealthPanel from "./SystemHealthPanel";
import TestResultsPanel from "./TestResultsPanel";
import UserManagementPanel from "./UserManagementPanel";

const Dashboard = () => {
    return (
        <div style={styles.dashboardContainer}>
            {/* Hardware Panel */}
            <div style={styles.panel}>
                <h2>Hardware Panel</h2>
                <HardwarePanel />
            </div>

            {/* Emulator Panel */}
            <div style={styles.panel}>
                <h2>Emulation Control</h2>
                <EmulatorPanel />
            </div>

            {/* MQTT Panel */}
            <div style={styles.panel}>
                <h2>MQTT Communication</h2>
                <MQTTPanel />
            </div>

            {/* Serial Panel */}
            <div style={styles.panel}>
                <h2>Serial Communication</h2>
                <SerialPanel />
            </div>

            {/* Live Metrics */}
            <div style={styles.panel}>
                <h2>Live System Metrics</h2>
                <LiveMetrics />
            </div>

            {/* Mirror Modal (Requires a topic) */}
            <div style={styles.panel}>
                <h2>Mirror Mode</h2>
                <MirrorModal topic="default/topic" onClose={() => console.log("Closing modal")} />
            </div>

            {/* Active Emulations */}
            <div style={styles.panel}>
                <h2>Active Emulations</h2>
                <ActiveEmulations />
            </div>

            {/* System Health Panel */}
            <div style={styles.panel}>
                <h2>System Health</h2>
                <SystemHealthPanel /> {/* System Health Panel */}
            </div>

            {/* Test Results Panel */}
            <div style={styles.panel}>
                <h2>Test Results</h2>
                <TestResultsPanel /> {/* Test Results Panel */}
            </div>

            {/* User Management Panel */}
            <div style={styles.panel}>
                <h2>User Management</h2>
                <UserManagementPanel /> {/* User Management Panel */}
            </div>
        </div>
    );
};

// Move styles to an object for better readability
const styles = {
    dashboardContainer: {
        display: "flex",
        flexWrap: "wrap", // Ensures panels stack on smaller screens
        justifyContent: "space-around",
        height: "100vh",
        padding: "10px",
        background: "#f0f0f0"
    },
    panel: {
        flex: "1 1 300px", // Ensures panels resize properly
        minWidth: "300px", // Prevents panels from shrinking too much
        padding: "15px",
        background: "#fff",
        boxShadow: "0 2px 5px rgba(0,0,0,0.2)",
        margin: "10px",
        borderRadius: "8px"
    }
};

export default Dashboard;
