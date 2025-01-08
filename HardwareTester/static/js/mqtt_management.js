document.addEventListener("DOMContentLoaded", () => {
    const mqttMessages = document.getElementById("mqtt-messages");
    const dashboardLiveFeed = document.getElementById("dashboard-live-feed");
    const testConnectionButton = document.getElementById("test-connection");
    const modal = new bootstrap.Modal(document.getElementById("dashboard-modal"));

    // Handle MQTT configuration submission
    document.getElementById("mqtt-config-form").addEventListener("submit", (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);

        fetch("/mqtt/connect", {
            method: "POST",
            body: new URLSearchParams(formData),
            headers: {
                "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content,
            },
        })
            .then((response) => response.json())
            .then((data) => {
                alert(data.message || "Configuration saved.");
            })
            .catch((error) => {
                console.error("Error connecting to MQTT:", error);
                alert("Failed to connect to MQTT broker.");
            });
    });

    // Handle Test Connection
    testConnectionButton.addEventListener("click", () => {
        fetch("/mqtt/test-connection", {
            method: "GET",
            headers: {
                "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content,
            },
        })
            .then((response) => response.json())
            .then((data) => {
                alert(data.message || "Test successful!");
            })
            .catch((error) => {
                console.error("Test connection failed:", error);
                alert("Test connection failed.");
            });
    });

    // Handle Live Dashboard Modal
    document.getElementById("toggle-dashboard-modal").addEventListener("click", () => {
        modal.show();
    });

    // WebSocket or Socket.IO for real-time updates
    const socket = io();

    socket.on("mqtt_message", (data) => {
        const messageElement = document.createElement("div");
        messageElement.textContent = `${data.topic}: ${data.message}`;
        mqttMessages.appendChild(messageElement);
        mqttMessages.scrollTop = mqttMessages.scrollHeight;

        // Update live feed in the dashboard modal
        const liveMessageElement = messageElement.cloneNode(true);
        dashboardLiveFeed.appendChild(liveMessageElement);
        dashboardLiveFeed.scrollTop = dashboardLiveFeed.scrollHeight;
    });
});
