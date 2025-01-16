import sys
import os
import unittest
from unittest.mock import patch
from flask import Flask, render_template_string, jsonify
from HardwareTester.views.main_views import main_bp

# Dynamically add the app folder to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../HardwareTester')))

class MainViewsTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and client."""
        app = Flask(__name__)
        app.register_blueprint(main_bp)
        app.config["TESTING"] = True
        self.app = app
        self.client = app.test_client()

        # HTML UI for previewing the home page dynamically
        self.template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Home Page Preview</title>
        </head>
        <body>
            <h1>Dynamic Home Page Preview</h1>
            <div>
                <label for="welcome-message">Welcome Message:</label>
                <input type="text" id="welcome-message" value="Welcome to Hardware Tester">
                <button onclick="updatePreview()">Update Preview</button>
            </div>

            <h2>Preview:</h2>
            <div id="preview">
                <h1>Welcome to Hardware Tester</h1>
            </div>

            <script>
                function updatePreview() {
                    const welcomeMessage = document.getElementById('welcome-message').value;
                    const preview = document.getElementById('preview');
                    preview.innerHTML = `<h1>${welcomeMessage}</h1>`;
                }
            </script>
        </body>
        </html>
        """

    def test_home_page(self):
        """Test rendering of the home page."""
       
