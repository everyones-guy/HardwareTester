import sys
import os
import unittest
from unittest.mock import patch
from flask import Flask, render_template_string, jsonify
from Hardware_Tester_App.views.emulator_views import emulator_bp

# Dynamically add the app folder to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Hardware_Tester_App')))

class EmulatorViewsTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and client."""
        app = Flask(__name__)
        app.register_blueprint(emulator_bp)
        app.config["TESTING"] = True
        self.app = app
        self.client = app.test_client()

        # HTML UI for real-time blueprints preview
        self.template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Emulator Blueprints Preview</title>
        </head>
        <body>
            <h1>Dynamic Emulator Blueprints Preview</h1>
            <div>
                <button onclick="fetchBlueprints()">Load Blueprints</button>
            </div>

            <h2>Preview:</h2>
            <div id="preview">
                <p>Blueprints will appear here.</p>
            </div>

            <script>
                async function fetchBlueprints() {
                    const response = await fetch('/emulator/blueprints-preview');
                    const data = await response.json();
                    const preview = document.getElementById('preview');
                    if (data.success) {
                        preview.innerHTML = `
                            <ul>
                                ${data.blueprints.map(bp => `<li>${bp}</li>`).join('')}
                            </ul>
                        `;
                    } else {
                        preview.innerHTML = `<p>Error: ${data.error}</p>`;
                    }
                }
            </script>
        </body>
        </html>
        """

    def test_emulator_blueprints(self):
        """Mock blueprints and verify rendering."""
        mock_blueprints = {
            "success": True,
            "blueprints": ["Blueprint A", "Blueprint B"]
        }
        with unittest.mock.patch("Hardware_Tester_App.services.emulator_service.EmulatorService.list_blueprints", return_value=mock_blueprints):
            response = self.client.get("/emulator/blueprints")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Blueprint A", response.data)

    def test_dynamic_blueprints_preview(self):
        """Test the real-time preview for emulator blueprints."""
        @self.app.route("/emulator/blueprints-preview", methods=["GET"])
        def blueprints_preview():
            """Mock the emulator blueprints preview endpoint."""
            mock_blueprints = {
                "success": True,
                "blueprints": ["Blueprint A", "Blueprint B"]
            }
            return jsonify(mock_blueprints)

        @self.app.route("/emulator/preview", methods=["GET"])
        def emulator_preview():
            """Serve the real-time emulator blueprints preview UI."""
            return render_template_string(self.template)

        # Test serving the preview interface
        with self.app.test_client() as client:
            response = client.get("/emulator/preview")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Dynamic Emulator Blueprints Preview", response.data)

if __name__ == "__main__":
    unittest.main()
