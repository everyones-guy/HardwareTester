// src/components/DeveloperToolsPanel.tsx
import React, { useState } from "react";
import Button from "@/components/common/Button";
import Card, { CardContent }  from "@/components/common/Card";
import { sendMQTTCommand } from "@/services/mqttService";
import axios from "@/services/axiosInstance";

const DeveloperToolsPanel: React.FC = () => {
    const [log, setLog] = useState<string[]>([]);
    const USE_FRONTEND_MQTT = import.meta.env.VITE_USE_FRONTEND_MQTT === "true";

    const pingDevice = async () => {
        const command = { action: "Ping" };
        const topic = "device/abc";

        try {
            if (USE_FRONTEND_MQTT) {
                sendMQTTCommand(topic, command);
                setLog((prev) => [...prev, "Sent Ping via frontend MQTT"]);
            } else {
                await axios.post("/mqtt/command", {
                    deviceId: "abc",
                    ...command,
                });
                setLog((prev) => [...prev, "Sent Ping via backend API"]);
            }
        } catch (err) {
            console.error("Ping failed:", err);
            setLog((prev) => [...prev, "Ping failed. Check console for details."]);
        }
    };

    return (
        <Card className="m-4 p-4 max-w-md">
            <CardContent>
                <h2 className="text-xl font-semibold mb-2">Developer Tools</h2>
                <Button onClick={pingDevice}>Send Ping</Button>
                <div className="mt-4 text-sm text-gray-600">
                    <strong>Log:</strong>
                    <ul className="list-disc list-inside">
                        {log.map((entry, idx) => (
                            <li key={idx}>{entry}</li>
                        ))}
                    </ul>
                </div>
            </CardContent>
        </Card>
    );
};

export default DeveloperToolsPanel;