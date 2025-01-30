import React, { useState, useEffect } from "react";
import { listenToMQTT, sendMQTTCommand, subscribeToTopic, unsubscribeFromTopic } from "../services/mqttService";
import "../styles.css";

const MirrorModal = ({ topic, onClose }) => {
    const [messages, setMessages] = useState([]);
    const [command, setCommand] = useState("");
    const [commandStatus, setCommandStatus] = useState(null);

    useEffect(() => {
        // Subscribe to MQTT topic
        const handleMessage = (message) => {
            setMessages((prev) => [...prev, message]);
        };

        subscribeToTopic(topic, handleMessage);
        listenToMQTT(topic, handleMessage);  // Real time updates

        return () => {
            unsubscribeFromTopic(topic); // Properly unsubscribe when closing
        };
    }, [topic]);

    const handleSendCommand = async () => {
        if (command.trim() === "") return;

        setCommandStatus("Sending...");
        try {
            await sendMQTTCommand(topic, { command });
            setCommandStatus("Command sent successfully!");
            setMessages((prev) => [...prev, `> Sent: ${command}`]);
        } catch (error) {
            setCommandStatus("Error: Failed to send command.");
        } finally {
            setCommand(""); // Clear input
            setTimeout(() => setCommandStatus(null), 3000); // Auto-clear status after 3 seconds
        }
    };

    return (
        <div className="modal">
            <h3>Mirror Mode: {topic}</h3>

            {/* Message Display */}
            <div className="message-box">
                {messages.length > 0 ? (
                    messages.map((msg, idx) => <div key={idx} className="message">{msg}</div>)
                ) : (
                    <p className="empty-state">No messages yet...</p>
                )}
            </div>

            {/* Command Input */}
            <div className="command-box">
                <input
                    type="text"
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    placeholder="Enter command"
                />
                <button onClick={handleSendCommand}>Send</button>
            </div>

            {/* Command Status */}
            {commandStatus && <p className="status">{commandStatus}</p>}

            <button className="close-btn" onClick={onClose}>Close</button>

        </div>
    );
};

export default MirrorModal;
