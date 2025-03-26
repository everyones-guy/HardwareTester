import unittest
from flask import Flask, Blueprint, render_template
from unittest.mock import patch
from Hardware_Tester_App.views.api_views import api_bp
from flask_wtf.csrf import generate_csrf



class APITestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and client."""
        #app = Flask(__name__)
        app = Flask(__name__, template_folder="C:/Users/Gary/source/repos/HardwareTester/Hardware_Tester_App/templates")  # Explicitly set template folder
        app.register_blueprint(api_bp, url_prefix="/api")
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test_secret_key"  # Set the secret key for CSRF
        self.client = app.test_client()
        self.app = app  # Save app instance for further use

         # Add CSRF token to test client
        with self.app.test_request_context():
            self.csrf_token = generate_csrf()


    def test_api_overview_page(self):
        """Test rendering of the API Overview page."""
        with self.app.test_request_context():
            response = self.client.get("/api/", headers={"X-CSRF-Token": self.csrf_token})
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"API Overview", response.data)



    @patch("Hardware_Tester_App.services.api_service.APIService.test_api_connection")
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
