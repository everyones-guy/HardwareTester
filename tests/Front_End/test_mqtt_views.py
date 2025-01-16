import sys
import os
import unittest
from unittest.mock import patch
from flask import Flask, render_template_string, jsonify, request
from HardwareTester.views.mqtt_views import mqtt_bp

# Dynamically add the app folder to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../HardwareTester')))

class MQTTViewsTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and client."""
        app = Flask(__name__)
        app.register_blueprint(mqtt_bp)
        app.config["TESTING"] = True
        self.app = app
        self.client = app.test_client()

        # HTML UI for modifying MQTT inputs dynamically
        self.template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>MQTT Test Input Modifier</title>
        </head>
        <body>
            <h1>MQTT Test Input Modifier</h1>
            <form id="mqtt-test-form">
                <label for="topic">MQTT Topic:</label>
                <input type="text" id="topic" value="test/topic">
                <br>
                <label for="message">MQTT Message:</label>
                <input type="text" id="message" value="Hello World">
                <br>
                <button type="button" onclick="sendMessage()">Publish Message</button>
            </form>

            <h2>Preview</h2>
            <div id="preview"></div>

            <script>
                function sendMessage() {
                    const topic = document.getElementById('topic').value;
                    const message = document.getElementById('message').value;

                    fetch('/mqtt-test/publish', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ topic: topic, message: message })
                    })
                    .then(response => response.json())
                    .then(data => {
                        const preview = document.getElementById('preview');
                        if (data.success) {
                            preview.innerHTML = `<p style="color: green;">Success: ${data.message}</p>`;
                        } else {
                            preview.innerHTML = `<p style="color: red;">Error: ${data.error || "Failed to publish message."}</p>`;
                        }
                    })
                    .catch(err => alert('Error publishing message: ' + err));
                }
            </script>
        </body>
        </html>
        """

    def test_publish_message(self):
        """Test publishing an MQTT message."""
        mock_response = {"success": True, "message": "Message published."}

        with patch("HardwareTester.services.mqtt_service.MQTTService.publish_message", return_value=mock_response):
            response = self.client.post("/mqtt/publish", json={"topic": "test/topic", "message": "Hello World"})
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Message published", response.data)

    def test_ui_dynamic_inputs(self):
        """Test the UI-driven dynamic input handling."""
        @self.app.route('/mqtt-test/publish', methods=['POST'])
        def publish_message():
            data = request.json
            topic = data.get("topic", "")
            message = data.get("message", "")
            if topic and message:
                return jsonify({"success": True, "message": f"Published to {topic}: {message}"})
            return jsonify({"success": False, "error": "Invalid input"}), 400

        # Serve the UI for modifying test inputs
        @self.app.route('/mqtt-test-ui', methods=['GET'])
        def test_ui():
            return render_template_string(self.template)

        # Mock and serve the dynamic test UI
        with self.app.test_client() as client:
            response = client.get('/mqtt-test-ui')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"MQTT Test Input Modifier", response.data)


if __name__ == "__main__":
    unittest.main()
