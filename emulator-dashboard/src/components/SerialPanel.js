import React, { useState, useEffect } from "react";

const SerialPanel = () => {
    const [ports, setPorts] = useState([]);
    const [selectedPort, setSelectedPort] = useState("");
    const [isConnected, setIsConnected] = useState(false);
    const [serialData, setSerialData] = useState("");
    const [message, setMessage] = useState("");

    useEffect(() => {
        // Fetch available serial ports from the backend
        fetch("/api/serial/ports")
            .then((response) => response.json())
            .then((data) => setPorts(data))
            .catch((error) => console.error("Error fetching ports:", error));
    }, []);

    const handleConnect = async () => {
        if (!selectedPort) {
            alert("Please select a serial port.");
            return;
        }

        try {
            const response = await fetch("/api/serial/connect", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ port: selectedPort }),
            });

            if (response.ok) {
                setIsConnected(true);
            } else {
                alert("Failed to connect.");
            }
        } catch (error) {
            console.error("Error connecting:", error);
        }
    };

    const handleDisconnect = async () => {
        try {
            const response = await fetch("/api/serial/disconnect", { method: "POST" });

            if (response.ok) {
                setIsConnected(false);
            } else {
                alert("Failed to disconnect.");
            }
        } catch (error) {
            console.error("Error disconnecting:", error);
        }
    };

    const handleSendData = async () => {
        if (!message.trim()) return;

        try {
            const response = await fetch("/api/serial/send", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message }),
            });

            if (response.ok) {
                setMessage("");
            } else {
                alert("Failed to send data.");
            }
        } catch (error) {
            console.error("Error sending data:", error);
        }
    };

    return (
        <div className="serial-panel">
            <h2>Serial Panel</h2>

            <div>
                <label>Select Port:</label>
                <select value={selectedPort} onChange={(e) => setSelectedPort(e.target.value)} disabled={isConnected}>
                    <option value="">-- Choose a port --</option>
                    {ports.map((port, index) => (
                        <option key={index} value={port}>
                            {port}
                        </option>
                    ))}
                </select>
            </div>

            <div>
                {!isConnected ? (
                    <button onClick={handleConnect} disabled={!selectedPort}>
                        Connect
                    </button>
                ) : (
                    <button onClick={handleDisconnect}>Disconnect</button>
                )}
            </div>

            <div>
                <h3>Send Data</h3>
                <input type="text" value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Enter message" />
                <button onClick={handleSendData} disabled={!isConnected}>
                    Send
                </button>
            </div>

            <div>
                <h3>Received Data</h3>
                <textarea value={serialData} readOnly rows="5" cols="40" />
            </div>
        </div>
    );
};

export default SerialPanel;
