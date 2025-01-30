import React, { useState, useEffect, useRef } from "react";
import mqtt from "mqtt";

const MQTTPanel = () => {
    // State management
    const [brokerUrl, setBrokerUrl] = useState("wss://test.mosquitto.org:8081");
    const [client, setClient] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [topic, setTopic] = useState("");
    const [message, setMessage] = useState("");
    const [receivedMessages, setReceivedMessages] = useState([]);
    const [subscribedTopics, setSubscribedTopics] = useState([]);
    const [scheduledMessages, setScheduledMessages] = useState([]);
    const eventTimeouts = useRef([]);

    // Initialize MQTT client
    useEffect(() => {
        return () => {
            if (client) {
                client.end();
            }
        };
    }, [client]);

    const handleConnect = () => {
        const mqttClient = mqtt.connect(brokerUrl, {
            clientId: `mqtt_client_${Math.random().toString(16).substr(2, 8)}`,
        });

        mqttClient.on("connect", () => {
            setIsConnected(true);
            console.log("Connected to MQTT Broker:", brokerUrl);
        });

        mqttClient.on("message", (receivedTopic, payload) => {
            const messageObj = {
                topic: receivedTopic,
                message: payload.toString(),
                timestamp: new Date().toLocaleTimeString(),
            };
            setReceivedMessages((prev) => [...prev, messageObj]);
        });

        mqttClient.on("error", (err) => {
            console.error("MQTT Error:", err);
            setIsConnected(false);
        });

        setClient(mqttClient);
    };

    const handleDisconnect = () => {
        if (client) {
            client.end();
            setIsConnected(false);
            setClient(null);
        }
    };

    const handleSubscribe = () => {
        if (client && topic) {
            client.subscribe(topic, (err) => {
                if (!err) {
                    setSubscribedTopics((prev) => [...prev, topic]);
                    console.log(`Subscribed to topic: ${topic}`);
                }
            });
        }
    };

    const handleUnsubscribe = (unsubscribeTopic) => {
        if (client) {
            client.unsubscribe(unsubscribeTopic, () => {
                setSubscribedTopics((prev) => prev.filter((t) => t !== unsubscribeTopic));
                console.log(`Unsubscribed from topic: ${unsubscribeTopic}`);
            });
        }
    };

    const handlePublish = () => {
        if (client && topic && message) {
            client.publish(topic, message);
            setMessage("");
        }
    };

    const scheduleMessage = (delay) => {
        if (!topic || !message) {
            alert("Enter topic and message before scheduling.");
            return;
        }
        const eventId = setTimeout(() => {
            handlePublish();
        }, delay);
        eventTimeouts.current.push(eventId);
        setScheduledMessages((prev) => [
            ...prev,
            { topic, message, delay, id: eventId, time: new Date().toLocaleTimeString() },
        ]);
    };

    const cancelScheduledMessages = () => {
        eventTimeouts.current.forEach((timeoutId) => clearTimeout(timeoutId));
        setScheduledMessages([]);
    };

    return (
        <div className="mqtt-panel">
            <h1>MQTT Communication Panel</h1>

            {/* Broker Connection */}
            <div>
                <label>Broker URL:</label>
                <input
                    type="text"
                    value={brokerUrl}
                    onChange={(e) => setBrokerUrl(e.target.value)}
                    placeholder="Enter broker URL"
                />
                {!isConnected ? (
                    <button onClick={handleConnect}>Connect</button>
                ) : (
                    <button onClick={handleDisconnect}>Disconnect</button>
                )}
            </div>

            {/* Topic Subscription */}
            <div>
                <label>Topic:</label>
                <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="Enter topic"
                    disabled={!isConnected}
                />
                <button onClick={handleSubscribe} disabled={!isConnected || !topic}>
                    Subscribe
                </button>
            </div>

            {/* Subscribed Topics */}
            <div>
                <h3>Subscribed Topics</h3>
                <ul>
                    {subscribedTopics.map((sub, index) => (
                        <li key={index}>
                            {sub}{" "}
                            <button onClick={() => handleUnsubscribe(sub)}>Unsubscribe</button>
                        </li>
                    ))}
                </ul>
            </div>

            {/* Publish Message */}
            <div>
                <label>Message:</label>
                <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Enter message"
                    disabled={!isConnected}
                />
                <button onClick={handlePublish} disabled={!isConnected || !topic || !message}>
                    Publish
                </button>
            </div>

            {/* Scheduled Messages */}
            <div>
                <h3>Scheduled Messages</h3>
                {scheduledMessages.map((msg, index) => (
                    <div key={index}>
                        <p>
                            <strong>Topic:</strong> {msg.topic}
                        </p>
                        <p>
                            <strong>Message:</strong> {msg.message}
                        </p>
                        <p>
                            <strong>Scheduled for:</strong> {msg.delay}ms at {msg.time}
                        </p>
                    </div>
                ))}
                <button onClick={() => scheduleMessage(5000)}>Schedule Message (5s)</button>
                <button onClick={cancelScheduledMessages}>Cancel Scheduled Messages</button>
            </div>

            {/* Received Messages */}
            <div>
                <h3>Received Messages</h3>
                <textarea value={receivedMessages.map(msg => `[${msg.timestamp}] ${msg.topic}: ${msg.message}`).join("\n")} readOnly rows="8" cols="50" />
            </div>
        </div>
    );
};

export default MQTTPanel;
