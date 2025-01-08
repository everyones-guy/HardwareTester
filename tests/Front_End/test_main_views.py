import unittest
from flask import Flask
from HardwareTester.views.main_views import main_bp

class MainViewsTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and client."""
        app = Flask(__name__)
        app.register_blueprint(main_bp)
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_home_page(self):
        """Test rendering of the home page."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome to Hardware Tester", response.data)

if __name__ == "__main__":
    unittest.main()
