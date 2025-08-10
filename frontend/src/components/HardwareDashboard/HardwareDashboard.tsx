import React from "react";
import HardwarePanel from "./HardwarePanel";
import HardwareMonitor from "./HardwareMonitor"; // optional future
import HardwareStats from "./HardwareStats"; // optional future
import "./HardwareDashboard.css";

const HardwareDashboard: React.FC = () => {
    return (
        <div className="hardware-dashboard">
            <h1>Hardware Dashboard</h1>

            <div className="hardware-section">
                <HardwarePanel />
            </div>

            /* <div className="hardware-section">
                <HardwareStats />
            </div> 
             <div className="hardware-section">
                <HardwareMonitor />
            </div>
        </div>
    );
};

export default HardwareDashboard;
