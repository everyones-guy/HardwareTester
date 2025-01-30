import mqtt from "mqtt";

const MQTT_BROKER = "ws://localhost:1883"; // Update this with your broker URL
const RECONNECT_INTERVAL = 5000; // Auto-reconnect delay (5 seconds)
const MAX_RECONNECT_ATTEMPTS = 10; // Limit reconnect attempts

let client = null;
let reconnectAttempts = 0;
let subscriptions = new Set();
let eventListeners = {};

/**
 * Initializes and connects to the MQTT broker.
 */
export const connectMQTT = () => {
    if (client && client.connected) {
        console.warn("MQTT already connected.");
        return;
    }

    console.log("Connecting to MQTT broker...");

    client = mqtt.connect(MQTT_BROKER, {
        reconnectPeriod: RECONNECT_INTERVAL,
        clientId: `emulator-${Math.random().toString(16).substr(2, 8)}`,
        clean: false, // Ensures persistent sessions
    });

    client.on("connect", () => {
        console.log("Connected to MQTT broker.");
        reconnectAttempts = 0;
        // Resubscribe to topics after reconnect
        subscriptions.forEach((topic) => client.subscribe(topic));
    });

    client.on("error", (error) => {
        console.error("MQTT Connection Error:", error);
        client.end();
        handleReconnect();
    });

    client.on("offline", () => {
        console.warn("MQTT is offline. Attempting to reconnect...");
        handleReconnect();
    });

    client.on("message", (topic, message) => {
        console.log(`Received MQTT message on ${topic}:`, message.toString());
        if (eventListeners[topic]) {
            eventListeners[topic].forEach((callback) => callback(message.toString()));
        }
    });
};

/**
 * Handles auto-reconnection logic.
 */
const handleReconnect = () => {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        console.error("Max MQTT reconnect attempts reached. Manual restart required.");
        return;
    }
    reconnectAttempts++;
    console.log(`Reconnecting to MQTT broker (Attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
    setTimeout(connectMQTT, RECONNECT_INTERVAL);
};

/**
 * Subscribes to a specific MQTT topic.
 * @param {string} topic - The topic to subscribe to.
 * @param {function} callback - Function to handle received messages.
 */
export const subscribeToTopic = (topic, callback) => {
    if (!client || !client.connected) {
        console.warn("Cannot subscribe. MQTT not connected.");
        return;
    }
    client.subscribe(topic, (err) => {
        if (!err) {
            console.log(`Subscribed to topic: ${topic}`);
            subscriptions.add(topic);
            if (!eventListeners[topic]) {
                eventListeners[topic] = [];
            }
            eventListeners[topic].push(callback);
        } else {
            console.error(`Error subscribing to topic ${topic}:`, err);
        }
    });
};

/**
 * Unsubscribes from a specific MQTT topic.
 * @param {string} topic - The topic to unsubscribe from.
 */
export const unsubscribeFromTopic = (topic) => {
    if (!client || !client.connected) {
        console.warn("Cannot unsubscribe. MQTT not connected.");
        return;
    }
    client.unsubscribe(topic, (err) => {
        if (!err) {
            console.log(`Unsubscribed from topic: ${topic}`);
            subscriptions.delete(topic);
            delete eventListeners[topic];
        } else {
            console.error(`Error unsubscribing from topic ${topic}:`, err);
        }
    });
};

/**
 * Publishes a message to an MQTT topic.
 * @param {string} topic - The topic to publish to.
 * @param {string} message - The message payload.
 */
export const publishMessage = (topic, message) => {
    if (!client || !client.connected) {
        console.warn("Cannot publish. MQTT not connected.");
        return;
    }
    client.publish(topic, message, { qos: 1 }, (err) => {
        if (!err) {
            console.log(`Published message to ${topic}: ${message}`);
        } else {
            console.error(`Error publishing to ${topic}:`, err);
        }
    });
};

/**
 * Sends a structured command message to a device.
 * @param {string} deviceTopic - The MQTT topic of the device.
 * @param {Object} command - The command object to send.
 */
export const sendMQTTCommand = (deviceTopic, command) => {
    if (!deviceTopic || !command) {
        console.error("Missing parameters for sendMQTTCommand");
        return;
    }
    publishMessage(deviceTopic, JSON.stringify(command));
};

/**
 * Disconnects from the MQTT broker.
 */
export const disconnectMQTT = () => {
    if (!client) return;
    console.log("Disconnecting from MQTT broker...");
    client.end();
};

/**
 * Listens for messages on a given topic.
 * @param {string} topic - The topic to listen to.
 * @param {function} callback - Function to execute when a message is received.
 */
export const listenToMQTT = (topic, callback) => {
    subscribeToTopic(topic, callback);
};

/**
 * Returns the current connection status of MQTT.
 * @returns {boolean} Whether MQTT is connected.
 */
export const isMQTTConnected = () => {
    return client && client.connected;
};
