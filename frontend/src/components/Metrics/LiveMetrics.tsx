import React, { useEffect, useState } from "react";
import "./LiveMetrics.css";

interface Metric {
    label: string;
    value: string | number;
    unit?: string;
    type?: "normal" | "warning" | "critical";
}

const LiveMetrics: React.FC = () => {
    const [metrics, setMetrics] = useState<Metric[]>([]);

    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                const res = await fetch("/metrics/live");
                const data = await res.json();
                setMetrics(data);
            } catch (err) {
                console.error("Error fetching live metrics:", err);
            }
        };

        fetchMetrics();
        const interval = setInterval(fetchMetrics, 5000); // refresh every 5s
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="live-metrics">
            <h3>Live System Metrics</h3>
            <div className="metric-grid">
                {metrics.map((m, idx) => (
                    <div key={idx} className={`metric-card ${m.type || "normal"}`}>
                        <div className="metric-label">{m.label}</div>
                        <div className="metric-value">
                            {m.value}
                            {m.unit && <span className="metric-unit"> {m.unit}</span>}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default LiveMetrics;
