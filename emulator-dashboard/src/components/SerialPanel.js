import React, { useState, useEffect, useRef } from "react";

const SerialPanel = () => {
    const [ports, setPorts] = useState([]);
    const [selectedPort, setSelectedPort] = useState("");
    const [baudRate, setBaudRate] = useState(115200);
    const [isConnected, setIsConnected] = useState(false);
    const [serialData, setSerialData] = useState([]);
    const [message, setMessage] = useState("");
    const [hexMode, setHexMode] = useState(false);
    const [autoReconnect, setAutoReconnect] = useState(true);
    const [commandHistory, setCommandHistory] = useState([]);
    const serialRef = useRef(null);

    let reconnectAttempts = 0;

    // Fetch available serial ports on mount
    useEffect(() => {
        fetch("/api/serial/ports")
            .then((res) => res.json())
            .then((data) => setPorts(data))
            .catch((error) => console.error("Error fetching ports:", error));
    }, []);

    // Connect to serial port
    const handleConnect = async () => {
        if (!selectedPort) return alert("Select a port first!");

        try {
            const response = await fetch("/api/serial/connect", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ port: selectedPort, baudRate }),
            });

            if (response.ok) {
                setIsConnected(true);
                listenToSerial();
                reconnectAttempts = 0; // Reset attempts on successful connection
            } else {
                alert("Failed to connect.");
            }
        } catch (error) {
            console.error("Connection error:", error);
        }
    };

    // Listen to serial data
    const listenToSerial = () => {
        if (!isConnected) return;

        serialRef.current = new EventSource("/api/serial/listen");

        serialRef.current.onmessage = (event) => {
            const incomingData = event.data;
            setSerialData((prev) => [...prev.slice(-49), incomingData]); // Keep only last 50 messages
        };

        serialRef.current.onerror = () => {
            console.error("Serial stream error.");
            if (autoReconnect && reconnectAttempts < 5) {
                console.log(`Reconnecting attempt #${reconnectAttempts + 1}...`);
                setTimeout(handleConnect, 2000 * (reconnectAttempts + 1));
                reconnectAttempts++;
            } else {
                console.warn("Max reconnect attempts reached.");
            }
        };
    };

    // Disconnect from serial port
    const handleDisconnect = async () => {
        try {
            await fetch("/api/serial/disconnect", { method: "POST" });
            setIsConnected(false);
            if (serialRef.current) serialRef.current.close();
        } catch (error) {
            console.error("Disconnection error:", error);
        }
    };

    // Send data over serial
    const handleSendData = async () => {
        if (!message.trim()) return;

        try {
            const formattedMessage = hexMode ? messageToHex(message) : message;
            await fetch("/api/serial/send", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: formattedMessage }),
            });

            setCommandHistory((prev) => [...prev.slice(-9), formattedMessage]); // Keep only last 10 commands
            setMessage("");
        } catch (error) {
            console.error("Error sending data:", error);
        }
    };

    // Convert text to hex
    const messageToHex = (text) => {
        return text.split("").map((char) => char.charCodeAt(0).toString(16)).join(" ");
    };

    return (
        <div className="serial-panel">
            <h2>Serial Communication Panel</h2>

            {/* Port Selection */}
            <div>
                <label>Serial Port:</label>
                <select value={selectedPort} onChange={(e) => setSelectedPort(e.target.value)} disabled={isConnected}>
                    <option value="">-- Select a port --</option>
                    {ports.map((port, index) => (
                        <option key={index} value={port}>
                            {port}
                        </option>
                    ))}
                </select>
            </div>

            {/* Baud Rate */}
            <div>
                <label>Baud Rate:</label>
                <input type="number" value={baudRate} onChange={(e) => setBaudRate(parseInt(e.target.value))} disabled={isConnected} />
            </div>

            {/* Connect/Disconnect */}
            <div>
                {!isConnected ? (
                    <button onClick={handleConnect} disabled={!selectedPort}>
                        Connect
                    </button>
                ) : (
                    <button onClick={handleDisconnect}>Disconnect</button>
                )}
            </div>

            {/* Hex Mode & Auto Reconnect */}
            <div>
                <label>
                    <input type="checkbox" checked={hexMode} onChange={() => setHexMode(!hexMode)} />
                    Hex Mode
                </label>
                <br />
                <label>
                    <input type="checkbox" checked={autoReconnect} onChange={() => setAutoReconnect(!autoReconnect)} />
                    Auto Reconnect
                </label>
            </div>

            {/* Send Data */}
            <div>
                <label>Send Message:</label>
                <input type="text" value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Enter message" disabled={!isConnected} />
                <button onClick={handleSendData} disabled={!isConnected || !message}>
                    Send
                </button>
            </div>

            {/* Received Data */}
            <div>
                <h3>Received Data</h3>
                <textarea value={serialData.join("\n")} readOnly rows="5" cols="50" />
            </div>

            {/* Command History */}
            <div>
                <h3>Command History</h3>
                <ul>
                    {commandHistory.map((cmd, index) => (
                        <li key={index}>{cmd}</li>
                    ))}
                </ul>
            </div>
        </div>
    );
};

export default SerialPanel;
