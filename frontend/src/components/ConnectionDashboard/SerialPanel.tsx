// src/components/ConnectionDashboard/SerialPanel.tsx
import React, { useState, useEffect, useRef } from "react";
import SerialService from "@/services/serialService";
import type { SerialDeviceInfo, SerialLogUpdate } from "@/types/serialTypes";
import "./SerialPanel.css";

const SerialPanel: React.FC = () => {
    const [ports, setPorts] = useState<SerialDeviceInfo[]>([]);
    const [selectedPort, setSelectedPort] = useState<string>("");
    const [baudRate, setBaudRate] = useState<number>(115200);
    const [isConnected, setIsConnected] = useState<boolean>(false);
    const [serialData, setSerialData] = useState<string[]>([]);
    const [message, setMessage] = useState<string>("");
    const [hexMode, setHexMode] = useState<boolean>(false);
    const [autoReconnect, setAutoReconnect] = useState<boolean>(true);

    const disconnectRef = useRef<() => void>();
    const reconnectAttempts = useRef<number>(0);
    const reconnectTimeoutId = useRef<number | null>(null);
    const unmounted = useRef(false);

    useEffect(() => {
        SerialService.listSerialPorts()
            .then((data) => setPorts(Array.isArray(data) ? data : []))
            .catch((err) => console.error("Error fetching ports:", err));

        // cleanup on unmount
        return () => {
            unmounted.current = true;
            disconnectRef.current?.();
            if (reconnectTimeoutId.current) {
                clearTimeout(reconnectTimeoutId.current);
            }
        };
    }, []);

    const handleConnect = async () => {
        if (!selectedPort) return alert("Select a port first!");
        try {
            const response = await SerialService.connectSerial(selectedPort, baudRate);
            if (response?.success) {
                setIsConnected(true);
                listenToSerial();
                reconnectAttempts.current = 0;
            } else {
                alert("Failed to connect.");
            }
        } catch (err) {
            console.error("Connection error:", err);
            maybeScheduleReconnect();
        }
    };

    const listenToSerial = () => {
        // tear down any previous listener before attaching a new one
        disconnectRef.current?.();
        disconnectRef.current = SerialService.subscribeToSerialLogs((log: SerialLogUpdate) => {
            const line = `[${log.timestamp}] ${log.data}`;
            setSerialData((prev) => [...prev.slice(-49), line]);
            // If your service signals disconnect/error via a special message, you could detect it here and call maybeScheduleReconnect()
        });
    };

    const handleDisconnect = async () => {
        try {
            await SerialService.disconnectSerial();
        } catch (err) {
            console.error("Disconnection error:", err);
        } finally {
            setIsConnected(false);
            disconnectRef.current?.();
            disconnectRef.current = undefined;
            if (reconnectTimeoutId.current) {
                clearTimeout(reconnectTimeoutId.current);
                reconnectTimeoutId.current = null;
            }
        }
    };

    const messageToHex = (text: string): string =>
        Array.from(text).map((c) => c.charCodeAt(0).toString(16).padStart(2, "0")).join(" ");

    const handleSendData = async () => {
        const raw = message.trim();
        if (!raw) return;
        try {
            const payload = hexMode ? messageToHex(raw) : raw;
            await SerialService.sendSerialData(payload);
            setCommandHistory((prev) => [...prev.slice(-9), payload]);
            setMessage("");
        } catch (err) {
            console.error("Send error:", err);
        }
    };

    // simple capped exponential backoff
    const maybeScheduleReconnect = () => {
        if (!autoReconnect || unmounted.current || isConnected) return;
        reconnectAttempts.current += 1;
        const base = 1000;
        const max = 15000;
        const delay = Math.min(max, base * Math.pow(2, reconnectAttempts.current - 1));
        const jitter = Math.floor(Math.random() * (delay / 2));
        const wait = delay - jitter;
        if (reconnectTimeoutId.current) clearTimeout(reconnectTimeoutId.current);
        reconnectTimeoutId.current = window.setTimeout(() => {
            if (!isConnected && !unmounted.current && selectedPort) {
                handleConnect();
            }
        }, wait);
    };

    const [commandHistory, setCommandHistory] = useState<string[]>([]);

    return (
        <div className="serial-panel">
            <h2>Serial Communication Panel</h2>

            <div>
                <label>Serial Port:</label>
                <select
                    value={selectedPort}
                    onChange={(e) => setSelectedPort(e.target.value)}
                    disabled={isConnected}
                >
                    <option value="">-- Select a port --</option>
                    {ports.map((port) => (
                        <option key={port.path} value={port.path}>
                            {port.path} {port.manufacturer ? `(${port.manufacturer})` : ""}
                        </option>
                    ))}
                </select>
            </div>

            <div>
                <label>Baud Rate:</label>
                <input
                    type="number"
                    value={baudRate}
                    onChange={(e) => setBaudRate(Number(e.target.value))}
                    disabled={isConnected}
                />
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
                <label>
                    <input
                        type="checkbox"
                        checked={hexMode}
                        onChange={() => setHexMode(!hexMode)}
                        disabled={!isConnected}
                    />
                    Hex Mode
                </label>
                <br />
                <label>
                    <input
                        type="checkbox"
                        checked={autoReconnect}
                        onChange={() => setAutoReconnect(!autoReconnect)}
                        disabled={isConnected}
                    />
                    Auto Reconnect
                </label>
            </div>

            <div>
                <label>Send Message:</label>
                <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Enter message"
                    disabled={!isConnected}
                />
                <button onClick={handleSendData} disabled={!isConnected || !message.trim()}>
                    Send
                </button>
            </div>

            <div>
                <h3>Received Data</h3>
                <textarea value={serialData.join("\n")} readOnly rows={5} cols={50} />
            </div>

            <div>
                <h3>Command History</h3>
                <ul>
                    {commandHistory.map((cmd, index) => (
                        <li key={`${cmd}-${index}`}>{cmd}</li>
                    ))}
                </ul>
            </div>
        </div>
    );
};

export default SerialPanel;
