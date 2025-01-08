import unittest
from flask import Flask
from HardwareTester.views.peripherals_views import peripherals_bp

class PeripheralsViewsTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and client."""
        app = Flask(__name__)
        app.register_blueprint(peripherals_bp)
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_list_peripherals(self):
        """Mock peripherals and verify rendering."""
        mock_peripherals = {
            "success": True,
            "peripherals": [{"id": 1, "name": "Peripheral A"}, {"id": 2, "name": "Peripheral B"}]
        }
        with unittest.mock.patch("HardwareTester.services.peripheral_service.PeripheralService.list_peripherals", return_value=mock_peripherals):
            response = self.client.get("/peripherals")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Peripheral A", response.data)

if __name__ == "__main__":
    unittest.main()
