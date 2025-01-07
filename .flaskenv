# .flaskenv

# Flask environment settings
FLASK_APP=HardwareTester:create_app  # Entry point for the Flask app
FLASK_ENV=development
FLASK_CONFIG=development
FLASK_DEBUG=1

# Database Configuration
DATABASE_URL=sqlite:///instance/app.db
SQLALCHEMY_DATABASE_URI=sqlite:///instance/app.db
SQLALCHEMY_TRACK_MODIFICATIONS=False

# Network settings
HOST=127.0.0.1
PORT=5000

# MQTT configuration
MQTT_BROKER=test.mosquitto.org
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TLS=False

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=app.log

# File upload settings
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16 MB
ALLOWED_SPEC_SHEET_EXTENSIONS=pdf,docx,xlsx
ALLOWED_TEST_PLAN_EXTENSIONS=pdf,csv,txt

# Other settings
DEFAULT_SERIAL_PORT=COM3
DEFAULT_BAUDRATE=9600

# Security settings
SESSION_COOKIE_SECURE=False
REMEMBER_COOKIE_SECURE=False
