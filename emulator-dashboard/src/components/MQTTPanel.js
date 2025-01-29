import React, { useState, useEffect } from "react";
import mqtt from "mqtt";

const MQTTPanel = () => {
    const [client, setClient] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [topic, setTopic] = useState("");
    const [message, setMessage] = useState("");
    const [receivedMessages, setReceivedMessages] = useState([]);

    useEffect(() => {
        return () => {
            if (client) {
                client.end();
            }
        };
    }, [client]);

    const handleConnect = () => {
        const mqttClient = mqtt.connect("wss://test.mosquitto.org:8081"); // Replace with your MQTT broker

        mqttClient.on("connect", () => {
            setIsConnected(true);
            console.log("Connected to MQTT Broker");
        });

        mqttClient.on("message", (receivedTopic, payload) => {
            setReceivedMessages((prev) => [...prev, `Topic: ${receivedTopic} | Message: ${payload.toString()}`]);
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
                if (err) {
                    console.error("Subscription error:", err);
                } else {
                    console.log(`Subscribed to topic: ${topic}`);
                }
            });
        }
    };

    const handlePublish = () => {
        if (client && topic && message) {
            client.publish(topic, message);
            setMessage("");
        }
    };

    return (
        <div className="mqtt-panel">
            <h2>MQTT Panel</h2>

            <div>
                {!isConnected ? (
                    <button onClick={handleConnect}>Connect to MQTT</button>
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
                <button onClick={handleSubscribe} disabled={!isConnected || !topic}>
                    Subscribe
                </button>
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
                <button onClick={handlePublish} disabled={!isConnected || !topic || !message}>
                    Publish
                </button>
            </div>

            <div>
                <h3>Received Messages</h3>
                <textarea value={receivedMessages.join("\n")} readOnly rows="5" cols="40" />
            </div>
        </div>
    );
};

export default MQTTPanel;
