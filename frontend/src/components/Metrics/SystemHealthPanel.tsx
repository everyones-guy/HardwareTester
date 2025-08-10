import React, { useEffect, useState } from "react";
import "./SystemHealthPanel.css";

interface HealthMetric {
    label: string;
    value: string | number;
    unit?: string;
    status?: "healthy" | "warning" | "critical";
}

const SystemHealthPanel: React.FC = () => {
    const [metrics, setMetrics] = useState<HealthMetric[]>([]);

    useEffect(() => {
        const fetchHealth = async () => {
            try {
                const res = await fetch("/system/health");
                const data = await res.json();
                setMetrics(data);
            } catch (err) {
                console.error("Error fetching system health:", err);
            }
        };

        fetchHealth();
        const interval = setInterval(fetchHealth, 10000); // poll every 10s
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="system-health-panel">
            <h3>System Health</h3>
            <div className="health-grid">
                {metrics.map((m, idx) => (
                    <div key={idx} className={`health-tile ${m.status || "healthy"}`}>
                        <div className="label">{m.label}</div>
                        <div className="value">
                            {m.value}
                            {m.unit && <span className="unit"> {m.unit}</span>}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default SystemHealthPanel;
