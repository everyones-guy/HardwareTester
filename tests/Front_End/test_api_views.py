import unittest
from flask import Flask
from unittest.mock import patch
from HardwareTester.views.api_views import api_bp


class APITestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and client."""
        app = Flask(__name__)
        app.register_blueprint(api_bp, url_prefix="/api")
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_api_overview_page(self):
        """Test rendering of the API Overview page."""
        response = self.client.get("/api/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"API Overview", response.data)

    @patch("HardwareTester.services.api_service.APIService.test_api_connection")
    def test_test_connection(self, mock_test_connection):
        """Test the test-connection endpoint."""
        mock_test_connection.return_value = {"success": True, "message": "Connection successful."}
        response = self.client.get("/api/test-connection")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Connection successful", response.data)

    def test_fetch_data_missing_field(self):
        """Test fetch-data with missing 'endpoint' field."""
        response = self.client.post("/api/fetch-data", json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Missing required field: 'endpoint'", response.data)


if __name__ == "__main__":
    unittest.main()
