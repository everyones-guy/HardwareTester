import React, { useState, useEffect, useRef } from "react";
import { Client as PahoMQTT } from "paho-mqtt"; 

const MQTTPanel = () => {
    const [brokerUrl, setBrokerUrl] = useState("wss://test.mosquitto.org:8081");
    const [client, setClient] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [topic, setTopic] = useState("");
    const [message, setMessage] = useState("");
    const [receivedMessages, setReceivedMessages] = useState([]);
    const [subscribedTopics, setSubscribedTopics] = useState([]);
    const [scheduledMessages, setScheduledMessages] = useState([]); // Schedule messages
    const eventTimeouts = useRef([]);

    // Initialize MQTT client
    useEffect(() => {
        return () => {
            if (client) {
                client.disconnect();
            }
        };
    }, [client]);

    const handleConnect = () => {
        const mqttClient = new PahoMQTT(brokerUrl, `mqtt_client_${Math.random().toString(16).substr(2, 8)}`);

        mqttClient.connect({
            onSuccess: () => {
                setIsConnected(true);
                setClient(mqttClient);
                console.log("Connected to MQTT Broker:", brokerUrl);
            },
            onFailure: (error) => {
                console.error("MQTT Connection Failed:", error);
                setIsConnected(false);
            },
        });

        mqttClient.onMessageArrived = (message) => {
            const messageObj = {
                topic: message.destinationName,
                message: message.payloadString,
                timestamp: new Date().toLocaleTimeString(),
            };
            setReceivedMessages((prev) => [...prev.slice(-49), messageObj]); // Only Keep last 50 messages
        };
    };

    const handleDisconnect = () => {
        if (client) {
            client.disconnect();
            setIsConnected(false);
            setClient(null);
        }
    };

    const handleSubscribe = () => {
        if (client && topic) {
            client.subscribe(topic);
            setSubscribedTopics((prev) => [...prev, topic]);
            console.log(`Subscribed to topic: ${topic}`);
        }
    };

    const handleUnsubscribe = (unsubscribeTopic) => {
        if (client) {
            client.unsubscribe(unsubscribeTopic);
            setSubscribedTopics((prev) => prev.filter((t) => t !== unsubscribeTopic));
            console.log(`Unsubscribed from topic: ${unsubscribeTopic}`);
        }
    };

    const handlePublish = () => {
        if (client && topic && message) {
            const mqttMessage = new PahoMQTT.Message(message);
            mqttMessage.destinationName = topic;
            client.send(mqttMessage);
            setMessage("");
        }
    };

    /**
     * Schedules a message to be sent after a delay.
     * @param {number} delay - Delay in milliseconds.
     */
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

    /**
     * Cancels all scheduled messages.
     */
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
                {scheduledMessages.length > 0 ? (
                    scheduledMessages.map((msg, index) => (
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
                    ))
                ) : (
                    <p>No scheduled messages.</p>
                )}
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
