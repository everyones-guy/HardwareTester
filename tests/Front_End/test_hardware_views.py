import unittest
from flask import Flask
from HardwareTester.views.hardware_views import hardware_bp

class HardwareViewsTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and client."""
        app = Flask(__name__)
        app.register_blueprint(hardware_bp)
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_discover_device(self):
        """Mock discovering a device."""
        mock_device = {
            "success": True,
            "device": {
                "id": 1,
                "name": "Device A",
                "status": "Online"
            }
        }
        with unittest.mock.patch("HardwareTester.services.hardware_service.HardwareService.discover_device", return_value=mock_device):
            response = self.client.post("/hardware/discover-device", json={"device_id": 1})
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Device A", response.data)

if __name__ == "__main__":
    unittest.main()
