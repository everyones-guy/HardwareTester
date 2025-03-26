import sys
import os
import unittest
from unittest.mock import patch
from flask import Flask, render_template_string
from Hardware_Tester_App.views.peripherals_views import peripherals_bp

# Dynamically add the app folder to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Hardware_Tester_App')))

class PeripheralsViewsTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and client."""
        app = Flask(__name__)
        app.register_blueprint(peripherals_bp)
        app.config["TESTING"] = True
        self.app = app
        self.client = app.test_client()

        # HTML UI for modifying inputs dynamically
        self.template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Test Input Modifier</title>
        </head>
        <body>
            <h1>Modify Test Inputs</h1>
            <form id="test-input-form">
                <label for="peripheral1">Peripheral 1 Name:</label>
                <input type="text" id="peripheral1" value="Peripheral A">
                <br>
                <label for="peripheral2">Peripheral 2 Name:</label>
                <input type="text" id="peripheral2" value="Peripheral B">
                <br>
                <button type="button" onclick="runTests()">Run Tests</button>
            </form>

            <script>
                function runTests() {
                    const peripheral1 = document.getElementById('peripheral1').value;
                    const peripheral2 = document.getElementById('peripheral2').value;

                    fetch('/run-tests', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            peripherals: [
                                { id: 1, name: peripheral1 },
                                { id: 2, name: peripheral2 }
                            ]
                        })
                    })
                    .then(response => response.json())
                    .then(data => alert(data.message))
                    .catch(err => alert('Error running tests: ' + err));
                }
            </script>
        </body>
        </html>
        """

    def test_list_peripherals(self):
        """Mock peripherals and verify rendering."""
        mock_peripherals = {
            "success": True,
            "peripherals": [
                {"id": 1, "name": "Peripheral A"},
                {"id": 2, "name": "Peripheral B"}
            ]
        }

        with patch("Hardware_Tester_App.services.peripheral_service.PeripheralService.list_peripherals", return_value=mock_peripherals):
            response = self.client.get("/peripherals")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Peripheral A", response.data)

    def test_ui_dynamic_inputs(self):
        """Test the UI-driven dynamic input handling."""
        @self.app.route('/run-tests', methods=['POST'])
        def run_tests():
            from flask import request, jsonify
            data = request.json
            peripherals = data.get("peripherals", [])
            if peripherals:
                return jsonify({"success": True, "message": f"Tested peripherals: {peripherals}"})
            return jsonify({"success": False, "message": "No peripherals provided"}), 400

        # Serve the UI for modifying test inputs
        @self.app.route('/test-ui', methods=['GET'])
        def test_ui():
            return render_template_string(self.template)

        # Mock peripherals and serve the dynamic test UI
        with self.app.test_client() as client:
            response = client.get('/test-ui')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Modify Test Inputs", response.data)


if __name__ == "__main__":
    unittest.main()
