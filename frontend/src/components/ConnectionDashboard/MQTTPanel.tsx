// src/components/ConnectionDashboard/MQTTPanel.tsx
import React, { useEffect, useRef, useState } from "react";
import { Client as PahoClient, Message as PahoMessage } from "paho-mqtt";
import "./MQTTPanel.css";

interface ReceivedMessage {
    topic: string;
    message: string;
    timestamp: string;
}

interface ScheduledMessage {
    topic: string;
    message: string;
    delay: number;
    id: number;   // browser setTimeout -> number
    time: string;
}

const MQTTPanel: React.FC = () => {
    const [brokerUrl, setBrokerUrl] = useState<string>("wss://test.mosquitto.org:8081");
    const [client, setClient] = useState<PahoClient | null>(null);
    const [isConnected, setIsConnected] = useState<boolean>(false);
    const [topic, setTopic] = useState<string>("");
    const [message, setMessage] = useState<string>("");
    const [receivedMessages, setReceivedMessages] = useState<ReceivedMessage[]>([]);
    const [subscribedTopics, setSubscribedTopics] = useState<string[]>([]);
    const [scheduledMessages, setScheduledMessages] = useState<ScheduledMessage[]>([]);
    const [autoReconnect, setAutoReconnect] = useState(true);

    const eventTimeouts = useRef<number[]>([]);
    const reconnectAttempt = useRef(0);
    const unmounted = useRef(false);

    useEffect(() => {
        return () => {
            unmounted.current = true;
            // cancel any scheduled timeouts
            eventTimeouts.current.forEach((id) => clearTimeout(id));
            // disconnect client if connected
            try {
                client?.disconnect();
            } catch { }
        };
    }, [client]);

    const attachHandlers = (c: PahoClient) => {
        c.onMessageArrived = (m: PahoMessage) => {
            const msg: ReceivedMessage = {
                topic: m.destinationName,
                message: m.payloadString,
                timestamp: new Date().toLocaleTimeString(),
            };
            setReceivedMessages((prev) => [...prev.slice(-99), msg]);
        };

        c.onConnectionLost = (resp) => {
            console.warn("MQTT connection lost:", resp?.errorMessage || resp);
            setIsConnected(false);
            if (autoReconnect && !unmounted.current) {
                // exponential backoff with cap
                reconnectAttempt.current += 1;
                const base = 1000;
                const max = 15000;
                const delay = Math.min(max, base * Math.pow(2, reconnectAttempt.current - 1));
                const jitter = Math.floor(Math.random() * (delay / 2));
                const wait = delay - jitter;

                const id = window.setTimeout(() => {
                    handleConnect(true); // silent try
                }, wait);
                eventTimeouts.current.push(id);
            }
        };
    };

    const handleConnect = (silent = false) => {
        if (client && isConnected) return; // already connected

        const clientId = `mqtt_${Math.random().toString(16).slice(2, 10)}`;

        // You can pass a full ws/wss URL directly to Paho Client
        const mqttClient = new PahoClient(brokerUrl, clientId);
        attachHandlers(mqttClient);

        mqttClient.connect({
            // If you use wss, useSSL is auto, but harmless to set:
            useSSL: brokerUrl.startsWith("wss://"),
            keepAliveInterval: 30,
            cleanSession: true,
            timeout: 5,
            onSuccess: () => {
                reconnectAttempt.current = 0;
                if (!silent) console.log("Connected to MQTT Broker:", brokerUrl);
                setIsConnected(true);
                setClient(mqttClient);
            },
            onFailure: (error) => {
                setIsConnected(false);
                if (!silent) console.error("MQTT Connection Failed:", error);
                if (autoReconnect && !unmounted.current) {
                    // trigger connectionLost path (backoff) manually
                    mqttClient?.onConnectionLost?.(error as any);
                }
            },
        });
    };

    const handleDisconnect = () => {
        reconnectAttempt.current = 0;
        eventTimeouts.current.forEach((id) => clearTimeout(id));
        eventTimeouts.current = [];
        try {
            client?.disconnect();
        } catch { }
        setIsConnected(false);
        setClient(null);
    };

    const handleSubscribe = () => {
        const t = topic.trim();
        if (!client || !t) return;
        if (!subscribedTopics.includes(t)) {
            client.subscribe(t, { qos: 0 });
            setSubscribedTopics((prev) => [...prev, t]);
            console.log(`Subscribed to topic: ${t}`);
        }
    };

    const handleUnsubscribe = (unsubscribeTopic: string) => {
        if (!client) return;
        client.unsubscribe(unsubscribeTopic);
        setSubscribedTopics((prev) => prev.filter((t) => t !== unsubscribeTopic));
        console.log(`Unsubscribed from topic: ${unsubscribeTopic}`);
    };

    const handlePublish = () => {
        const t = topic.trim();
        const msg = message;
        if (!client || !t || !msg) return;
        const mqttMessage = new PahoMessage(msg);
        mqttMessage.destinationName = t;
        client.send(mqttMessage);
        setMessage("");
    };

    const scheduleMessage = (delay: number) => {
        const t = topic.trim();
        const msg = message;
        if (!t || !msg) {
            alert("Enter topic and message before scheduling.");
            return;
        }
        const id = window.setTimeout(() => {
            handlePublish();
        }, delay);
        eventTimeouts.current.push(id);
        setScheduledMessages((prev) => [
            ...prev,
            { topic: t, message: msg, delay, id, time: new Date().toLocaleTimeString() },
        ]);
    };

    const cancelScheduledMessages = () => {
        eventTimeouts.current.forEach((timeoutId) => clearTimeout(timeoutId));
        eventTimeouts.current = [];
        setScheduledMessages([]);
    };

    return (
        <div className="mqtt-panel">
            <h2>MQTT Communication Panel</h2>

            <div>
                <label>Broker URL:</label>
                <input
                    type="text"
                    value={brokerUrl}
                    onChange={(e) => setBrokerUrl(e.target.value)}
                    placeholder="wss://host:port[/path]"
                />
                {!isConnected ? (
                    <button onClick={() => handleConnect(false)}>Connect</button>
                ) : (
                    <button onClick={handleDisconnect}>Disconnect</button>
                )}
            </div>

            <div>
                <label>Topic:</label>
                <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="Enter topic"
                    disabled={!isConnected}
                />
                <button onClick={handleSubscribe} disabled={!isConnected || !topic.trim()}>
                    Subscribe
                </button>
            </div>

            <div>
                <h3>Subscribed Topics</h3>
                <ul>
                    {subscribedTopics.map((sub) => (
                        <li key={sub}>
                            {sub} <button onClick={() => handleUnsubscribe(sub)}>Unsubscribe</button>
                        </li>
                    ))}
                </ul>
            </div>

            <div>
                <label>Message:</label>
                <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Enter message"
                    disabled={!isConnected}
                />
                <button onClick={handlePublish} disabled={!isConnected || !topic.trim() || !message}>
                    Publish
                </button>
            </div>

            <div>
                <h3>Scheduled Messages</h3>
                {scheduledMessages.length > 0 ? (
                    scheduledMessages.map((msg) => (
                        <div key={msg.id}>
                            <p><strong>Topic:</strong> {msg.topic}</p>
                            <p><strong>Message:</strong> {msg.message}</p>
                            <p><strong>Scheduled for:</strong> {msg.delay}ms at {msg.time}</p>
                        </div>
                    ))
                ) : (
                    <p>No scheduled messages.</p>
                )}
                <button onClick={() => scheduleMessage(5000)}>Schedule Message (5s)</button>
                <button onClick={cancelScheduledMessages}>Cancel Scheduled Messages</button>
            </div>

            <div>
                <h3>Received Messages</h3>
                <textarea
                    value={receivedMessages
                        .map((m) => `[${m.timestamp}] ${m.topic}: ${m.message}`)
                        .join("\n")}
                    readOnly
                    rows={8}
                    cols={50}
                />
            </div>

            <label className="bt-toggle" style={{ marginTop: 8 }}>
                <input
                    type="checkbox"
                    checked={autoReconnect}
                    onChange={() => setAutoReconnect((v) => !v)}
                    disabled={isConnected} // optional: freeze while connected
                />
                Auto Reconnect
            </label>
        </div>
    );
};

export default MQTTPanel;
