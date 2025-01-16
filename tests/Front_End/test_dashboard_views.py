
import unittest
from flask import Flask
from HardwareTester.views.dashboard_views import dashboard_bp

class DashboardViewsTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and client."""
        app = Flask(__name__)
        app.register_blueprint(dashboard_bp)
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_dashboard_home(self):
        """Test rendering of the dashboard home page."""
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dashboard Overview", response.data)

if __name__ == "__main__":
    unittest.main()
