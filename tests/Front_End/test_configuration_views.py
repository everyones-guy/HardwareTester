import unittest
from unittest.mock import patch
from flask import Flask
from HardwareTester.views.configuration_views import configuration_bp


class ConfigurationViewsTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and client."""
        app = Flask(__name__)
        app.register_blueprint(configuration_bp, url_prefix="/configurations")
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_configuration_management_page(self):
        """Test rendering of the configuration management page."""
        response = self.client.get("/configurations/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Configuration Management", response.data)

    def test_list_configurations(self):
        """Mock configurations list and verify rendering."""
        mock_configs = {
            "success": True,
            "configurations": [
                {"id": 1, "name": "Config A"},
                {"id": 2, "name": "Config B"},
            ],
        }

        with patch(
            "HardwareTester.services.configuration_service.ConfigurationService.load_configuration",
            return_value=mock_configs,
        ):
            response = self.client.get("/configurations/load")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Config A", response.data)

    def test_preview_configuration(self):
        """Mock configuration preview rendering."""
        mock_preview = {
            "success": True,
            "preview": "<div>Preview: Config A</div>",
        }

        with patch(
            "HardwareTester.services.configuration_service.ConfigurationService.generate_preview",
            return_value=mock_preview,
        ):
            response = self.client.get("/configurations/preview/1")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Preview: Config A", response.data)


if __name__ == "__main__":
    unittest.main()
