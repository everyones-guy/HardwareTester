import React, { useState, useEffect } from "react";
import { listenToMQTT } from "../services/mqttService";

const LiveMetrics = ({ topics }) => {
    const [metrics, setMetrics] = useState({});

    useEffect(() => {
        const unsubscribeFunctions = topics.map((topic) =>
            listenToMQTT(topic, (message) => {
                setMetrics((prev) => ({
                    ...prev,
                    [topic]: JSON.parse(message), // Assuming metrics are sent as JSON
                }));
            })
        );

        return () => unsubscribeFunctions.forEach((unsubscribe) => unsubscribe());
    }, [topics]);

    return (
        <div style={{ height: "200px", overflowY: "scroll", background: "#1e1e1e", color: "#00ff00", padding: "10px" }}>
            <h3>Live Metrics</h3>
            {Object.entries(metrics).map(([topic, data]) => (
                <div key={topic}>
                    <strong>{topic}:</strong> {JSON.stringify(data)}
                </div>
            ))}
        </div>
    );
};

export default LiveMetrics;
