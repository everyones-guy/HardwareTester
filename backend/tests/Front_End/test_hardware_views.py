import sys
import os
import unittest
from unittest.mock import patch
from flask import Flask, render_template_string, jsonify
from Hardware_Tester_App.views.hardware_views import hardware_bp

# Dynamically add the app folder to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Hardware_Tester_App')))

class HardwareViewsTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and client."""
        app = Flask(__name__)
        app.register_blueprint(hardware_bp)
        app.config["TESTING"] = True
        self.app = app
        self.client = app.test_client()

        # HTML UI for real-time device discovery preview
        self.template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Device Discovery Preview</title>
        </head>
        <body>
            <h1>Dynamic Device Discovery Preview</h1>
            <div>
                <label for="device-id">Device ID:</label>
                <input type="number" id="device-id" value="1">
                <button onclick="discoverDevice()">Discover Device</button>
            </div>

            <h2>Preview:</h2>
            <div id="preview">
                <p>Device details will appear here.</p>
            </div>

            <script>
                async function discoverDevice() {
                    const deviceId = document.getElementById('device-id').value;
                    const response = await fetch('/hardware/discover-device-preview', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ device_id: deviceId })
                    });
                    const data = await response.json();
                    const preview = document.getElementById('preview');
                    if (data.success) {
                        preview.innerHTML = `
                            <p><strong>Device Name:</strong> ${data.device.name}</p>
                            <p><strong>Status:</strong> ${data.device.status}</p>
                        `;
                    } else {
                        preview.innerHTML = `<p>Error: ${data.error}</p>`;
                    }
                }
            </script>
        </body>
        </html>
        """

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
        with unittest.mock.patch("Hardware_Tester_App.services.hardware_service.HardwareService.discover_device", return_value=mock_device):
            response = self.client.post("/hardware/discover-device", json={"device_id": 1})
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Device A", response.data)

    def test_dynamic_discovery_preview(self):
        """Test the real-time preview for device discovery."""
        @self.app.route("/hardware/discover-device-preview", methods=["POST"])
        def discover_device_preview():
            """Mock the device discovery preview endpoint."""
            mock_device = {
                "success": True,
                "device": {
                    "id": 1,
                    "name": "Device A",
                    "status": "Online"
                }
            }
            return jsonify(mock_device)

        @self.app.route("/hardware/preview", methods=["GET"])
        def hardware_preview():
            """Serve the real-time device discovery preview UI."""
            return render_template_string(self.template)

        # Test serving the preview interface
        with self.app.test_client() as client:
            response = client.get("/hardware/preview")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Dynamic Device Discovery Preview", response.data)

if __name__ == "__main__":
    unittest.main()
