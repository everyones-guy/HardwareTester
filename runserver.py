"""
This script runs the HardwareTester application using a development server.
"""

import os
import sys
from dotenv import load_dotenv
from HardwareTester import create_app
from HardwareTester.extensions import socketio

# Load environment variables from .env file
load_dotenv()

# Dynamically adjust path to include the project root
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Retrieve environment variables
config_name = os.getenv("FLASK_ENV", "development")
host = os.getenv("HOST", "127.0.0.1")
port = int(os.getenv("PORT", 5000))
debug = os.getenv("DEBUG", "False").lower() in ["true", "1", "t"]

# Create the Flask application
app = create_app(config_name)

if __name__ == "__main__":
    # Run the application with WebSocket support
    socketio.run(app, host=host, port=port, debug=debug)
