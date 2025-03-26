document.addEventListener("DOMContentLoaded", () => {
    const mqttMessages = document.getElementById("mqtt-messages");
    const dashboardLiveFeed = document.getElementById("dashboard-live-feed");
    const testConnectionButton = document.getElementById("test-connection");
    const modal = new bootstrap.Modal(document.getElementById("dashboard-modal"));

    /**
     * Handle MQTT Configuration Submission
     */
    document.getElementById("mqtt-config-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const payload = Object.fromEntries(formData.entries());

        try {
            const response = await apiCall("/mqtt/connect", "POST", payload);
            alert(response.message || "Configuration saved.");
        } catch (error) {
            console.error("Error connecting to MQTT:", error);
            alert("Failed to connect to MQTT broker.");
        }
    });

    /**
     * Handle MQTT Test Connection
     */
    testConnectionButton.addEventListener("click", async () => {
        try {
            const response = await apiCall("/mqtt/test-connection", "GET");
            alert(response.message || "Test successful!");
        } catch (error) {
            console.error("Test connection failed:", error);
            alert("Test connection failed.");
        }
    });

    /**
     * Toggle Live Dashboard Modal
     */
    document.getElementById("toggle-dashboard-modal").addEventListener("click", () => {
        modal.show();
    });

    /**
     * WebSocket Handling for Real-Time MQTT Messages
     */
    const socket = io();

    socket.on("mqtt_message", (data) => {
        addMqttMessage(mqttMessages, data.topic, data.message);
        addMqttMessage(dashboardLiveFeed, data.topic, data.message);
    });

    /**
     * Append new messages dynamically & keep UI responsive
     */
    function addMqttMessage(container, topic, message) {
        if (!container) return;

        const messageElement = document.createElement("div");
        messageElement.innerHTML = `<strong>${topic}</strong>: ${message}`;
        container.appendChild(messageElement);

        // Keep scroll at the bottom
        container.scrollTop = container.scrollHeight;
    }
});
