import React, { useEffect, useState } from "react";
import "./HardwareMonitor.css";

interface MonitorEvent {
    timestamp: string;
    message: string;
    type: "info" | "warning" | "error";
}

const HardwareMonitor: React.FC = () => {
    const [events, setEvents] = useState<MonitorEvent[]>([]);

    useEffect(() => {
        // Replace this with WebSocket or polling later
        const fakeInterval = setInterval(() => {
            const now = new Date().toLocaleTimeString();
            const types = ["info", "warning", "error"] as const;
            const randomType = types[Math.floor(Math.random() * types.length)];
            const newEvent: MonitorEvent = {
                timestamp: now,
                message: `Mock event at ${now}`,
                type: randomType,
            };
            setEvents((prev) => [...prev.slice(-49), newEvent]);
        }, 3000);

        return () => clearInterval(fakeInterval);
    }, []);

    return (
        <div className="hardware-monitor">
            <h2>Live Monitor</h2>
            <ul className="event-log">
                {events.map((e, idx) => (
                    <li key={idx} className={`event ${e.type}`}>
                        <span className="time">[{e.timestamp}]</span> {e.message}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default HardwareMonitor;
