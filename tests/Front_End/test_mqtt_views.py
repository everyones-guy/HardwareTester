import unittest
from flask import Flask
from HardwareTester.views.mqtt_views import mqtt_bp

class MQTTViewsTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and client."""
        app = Flask(__name__)
        app.register_blueprint(mqtt_bp)
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_publish_message(self):
        """Test publishing an MQTT message."""
        mock_response = {"success": True, "message": "Message published."}
        with unittest.mock.patch("HardwareTester.services.mqtt_service.MQTTService.publish_message", return_value=mock_response):
            response = self.client.post("/mqtt/publish", json={"topic": "test/topic", "message": "Hello World"})
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Message published", response.data)

if __name__ == "__main__":
    unittest.main()
