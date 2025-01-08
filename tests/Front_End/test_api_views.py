import unittest
from flask import Flask
from HardwareTester.views.api_views import api_bp

class APITestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and client."""
        app = Flask(__name__)
        app.register_blueprint(api_bp)
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_api_overview(self):
        """Test the API overview endpoint."""
        response = self.client.get("/api/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"API Overview", response.data)

if __name__ == "__main__":
    unittest.main()
