import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from HardwareTester.views.configuration_views import configuration_bp


class ConfigurationViewsTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and test client."""
        self.app = Flask(__name__)
        self.app.register_blueprint(configuration_bp, url_prefix="/configurations")
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_configuration_management_page(self):
        """Test rendering of the configuration management page."""
        with patch(
            "flask.render_template",
            return_value="<h1>Configuration Management</h1>",
        ) as mock_render_template:
            response = self.client.get("/configurations/")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Configuration Management", response.data)
            mock_render_template.assert_called_once_with("configuration_management.html")

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
            "HardwareTester.services.configuration_service.ConfigurationService.list_configurations",
            return_value=mock_configs,
        ) as mock_list_configs:
            response = self.client.get("/configurations/list")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Config A", response.data)
            mock_list_configs.assert_called_once()

    def test_preview_configuration(self):
        """Mock configuration preview rendering."""
        mock_preview = {
            "success": True,
            "preview": "<div>Preview: Config A</div>",
        }

        with patch(
            "HardwareTester.services.configuration_service.ConfigurationService.generate_preview",
            return_value=mock_preview,
        ) as mock_generate_preview:
            response = self.client.get("/configurations/preview/1")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Preview: Config A", response.data)
            mock_generate_preview.assert_called_once_with(1)

    def test_save_configuration(self):
        """Mock saving a configuration and verify the response."""
        mock_response = {
            "success": True,
            "message": "Configuration saved successfully.",
        }

        with patch(
            "HardwareTester.services.configuration_service.ConfigurationService.save_configuration",
            return_value=mock_response,
        ) as mock_save_configuration:
            response = self.client.post(
                "/configurations/save",
                json={"name": "Test Config", "layout": {"key": "value"}},
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Configuration saved successfully.", response.data)
            mock_save_configuration.assert_called_once_with(
                {"name": "Test Config", "layout": {"key": "value"}}
            )

    def test_load_configuration(self):
        """Mock loading a specific configuration."""
        mock_config = {
            "success": True,
            "configuration": {"name": "Config A", "layout": {"key": "value"}},
        }

        with patch(
            "HardwareTester.services.configuration_service.ConfigurationService.load_configuration",
            return_value=mock_config,
        ) as mock_load_configuration:
            response = self.client.get("/configurations/load/1")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Config A", response.data)
            mock_load_configuration.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
