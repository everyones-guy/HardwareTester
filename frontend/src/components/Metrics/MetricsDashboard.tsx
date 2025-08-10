import React from "react";
import LiveMetrics from "./LiveMetrics";
import HardwareLogsMetrics from "./HardwareLogsMetrics";
import SystemHealthPanel from "./SystemHealthPanel";

import "./MetricsDashboard.css";

const MetricsDashboard: React.FC = () => {
    return (
        <div className="metrics-dashboard">
            <h1>System Metrics</h1>

            <div className="metrics-section">
                <SystemHealthPanel />
            </div>

            <div className="metrics-section">
                <LiveMetrics />
            </div>

            <div className="metrics-section">
                <HardwareLogsMetrics />
            </div>

            {/* Future metrics:
            <div className="metrics-section">
                <PerformanceCharts />
            </div>
            */}
        </div>
    );
};

export default MetricsDashboard;
