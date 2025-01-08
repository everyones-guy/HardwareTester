import unittest
from flask import Flask
from HardwareTester.views.configuration_views import configuration_bp

class ConfigurationViewsTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and client."""
        app = Flask(__name__)
        app.register_blueprint(configuration_bp)
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_list_configurations(self):
        """Mock configurations list and verify rendering."""
        mock_configs = {
            "success": True,
            "configurations": [
                {"id": 1, "name": "Config A"},
                {"id": 2, "name": "Config B"}
            ]
        }
        with unittest.mock.patch("HardwareTester.services.configuration_service.ConfigurationService.list_configurations", return_value=mock_configs):
            response = self.client.get("/configurations")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Config A", response.data)

if __name__ == "__main__":
    unittest.main()
