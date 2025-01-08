import unittest
from unittest.mock import patch
from flask import Flask, Blueprint, render_template_string
from HardwareTester.views.api_views import api_bp
import json

class APITestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and client with a preview interface."""
        app = Flask(__name__)
        app.register_blueprint(api_bp, url_prefix="/api")
        app.config["TESTING"] = True

        # Create a preview endpoint
        @app.route("/test-preview/api", methods=["GET"])
        def preview():
            # Mock data for preview
            mock_data = {"endpoint": "/api", "description": "API Overview"}
            return render_template_string(
                """
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>API Test Preview</title>
                    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css">
                    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/js/bootstrap.bundle.min.js"></script>
                </head>
                <body class="p-4">
                    <div class="container">
                        <h1 class="text-center">API Test Preview</h1>
                        <form id="api-test-form" class="mb-4">
                            <div class="mb-3">
                                <label for="endpoint" class="form-label">API Endpoint</label>
                                <input type="text" id="endpoint" name="endpoint" class="form-control" value="{{ mock_data.endpoint }}" required>
                            </div>
                            <div class="mb-3">
                                <label for="description" class="form-label">Description</label>
                                <input type="text" id="description" name="description" class="form-control" value="{{ mock_data.description }}" required>
                            </div>
                            <button type="button" class="btn btn-primary w-100" onclick="runTest()">Run Test</button>
                        </form>
                        <h3>Results</h3>
                        <div id="test-results" class="border p-3 bg-light">
                            <!-- Results will appear here -->
                        </div>
                    </div>
                    <script>
                        function runTest() {
                            const endpoint = document.getElementById("endpoint").value;
                            const description = document.getElementById("description").value;

                            fetch(endpoint)
                                .then(response => {
                                    const resultDiv = document.getElementById("test-results");
                                    if (response.ok) {
                                        resultDiv.innerHTML = `<div class="alert alert-success">
                                            <strong>Success:</strong> ${description} fetched successfully from ${endpoint}.
                                        </div>`;
                                    } else {
                                        resultDiv.innerHTML = `<div class="alert alert-danger">
                                            <strong>Error:</strong> Failed to fetch data from ${endpoint}.
                                        </div>`;
                                    }
                                })
                                .catch(error => {
                                    document.getElementById("test-results").innerHTML = `<div class="alert alert-danger">
                                        <strong>Error:</strong> ${error.message}
                                    </div>`;
                                });
                        }
                    </script>
                </body>
                </html>
                """,
                mock_data=mock_data,
            )

        self.client = app.test_client()

    def test_api_overview(self):
        """Test the API overview endpoint."""
        with patch("HardwareTester.services.api_service.APIService.get_overview", return_value={"message": "API Overview"}):
            response = self.client.get("/api/")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"API Overview", response.data)

    def test_preview(self):
        """Verify the preview window is accessible."""
        response = self.client.get("/test-preview/api")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"API Test Preview", response.data)

if __name__ == "__main__":
    unittest.main()
