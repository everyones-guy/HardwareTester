import React, { useState, useEffect } from "react";
import { listenToMQTT, sendMQTTCommand } from "../services/mqttService";

const MirrorModal = ({ topic, onClose }) => {
    const [messages, setMessages] = useState([]);
    const [command, setCommand] = useState("");
    const [commandStatus, setCommandStatus] = useState(null);

    useEffect(() => {
        const unsubscribe = listenToMQTT(topic, (message) => {
            setMessages((prev) => [...prev, message]);
        });

        return () => unsubscribe();
    }, [topic]);

    const handleSendCommand = async () => {
        if (command.trim() === "") return;

        setCommandStatus("Sending...");
        try {
            await sendMQTTCommand(topic, command);
            setCommandStatus("Success: Command sent!");
            setMessages((prev) => [...prev, `> Sent: ${command}`]);
        } catch (error) {
            setCommandStatus("Error: Failed to send command.");
        } finally {
            setCommand(""); // Clear input
            setTimeout(() => setCommandStatus(null), 3000); // Clear status after 3 seconds
        }
    };

    return (
        <div className="modal" style={{ padding: "10px", background: "#fff", border: "1px solid #ccc" }}>
            <h3>Mirror Mode: {topic}</h3>
            <div style={{ height: "200px", overflowY: "scroll", background: "#f0f0f0", padding: "5px" }}>
                {messages.map((msg, idx) => (
                    <div key={idx}>{msg}</div>
                ))}
            </div>
            <div>
                <input
                    type="text"
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    placeholder="Enter command"
                    style={{ width: "calc(100% - 50px)", marginRight: "10px" }}
                />
                <button onClick={handleSendCommand}>Send</button>
            </div>
            {commandStatus && <p>{commandStatus}</p>}
            <button onClick={onClose}>Close</button>
        </div>
    );
};

export default MirrorModal;
