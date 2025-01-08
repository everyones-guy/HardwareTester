import unittest
from flask import Flask
from HardwareTester.views.emulator_views import emulator_bp

class EmulatorViewsTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and client."""
        app = Flask(__name__)
        app.register_blueprint(emulator_bp)
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_emulator_blueprints(self):
        """Mock blueprints and verify rendering."""
        mock_blueprints = {
            "success": True,
            "blueprints": ["Blueprint A", "Blueprint B"]
        }
        with unittest.mock.patch("HardwareTester.services.emulator_service.EmulatorService.list_blueprints", return_value=mock_blueprints):
            response = self.client.get("/emulator/blueprints")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Blueprint A", response.data)

if __name__ == "__main__":
    unittest.main()
