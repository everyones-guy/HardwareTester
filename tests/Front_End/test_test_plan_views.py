
from flask import Flask
from flask.testing import FlaskClient
import unittest
from HardwareTester.views.test_plan_views import test_plan_bp

class TestPlanViewsTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask test app and client."""
        app = Flask(__name__)
        app.register_blueprint(test_plan_bp)
        app.config["TESTING"] = True
        self.client: FlaskClient = app.test_client()

    def test_show_test_plans(self):
        """Test rendering of the test plan management page."""
        response = self.client.get("/test-plans")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test Plan Management", response.data)

    def test_get_test_plans_list(self):
        """Mock the list of test plans and verify response."""
        mock_test_plans = {
            "success": True,
            "testPlans": [
                {"id": 1, "name": "Test Plan A", "uploaded_by": "Admin"},
                {"id": 2, "name": "Test Plan B", "uploaded_by": "User1"}
            ]
        }
        with self.client.application.app_context():
            with unittest.mock.patch("HardwareTester.services.test_plan_service.TestPlanService.list_tests", return_value=mock_test_plans):
                response = self.client.get("/test-plans/list")
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"Test Plan A", response.data)

    def test_preview_test_plan(self):
        """Test previewing a test plan."""
        mock_preview = {
            "success": True,
            "plan": {
                "id": 1,
                "name": "Test Plan A",
                "steps": ["Step 1: Open Valve", "Step 2: Close Valve"]
            }
        }
        with unittest.mock.patch("HardwareTester.services.test_plan_service.TestPlanService.preview_test_plan", return_value=mock_preview):
            response = self.client.get("/test-plans/1/preview")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Step 1: Open Valve", response.data)

if __name__ == "__main__":
    unittest.main()
