# .flaskenv

# Flask environment settings
FLASK_APP=HardwareTester:create_app  # Entry point for the Flask app
FLASK_ENV=development
FLASK_CONFIG=development
FLASK_DEBUG=1  # Set to 0 in production
TEMPLATES_FOLDER=C:/Users/Gary/source/repos/HardwareTester/HardwareTester/templates

# Database Configuration
# DATABASE_URL=sqlite:///instance/app.db  # Default SQLite database location
# SQLALCHEMY_DATABASE_URI=sqlite:///instance/app.db
# DATABASE_URL=sqlite:///C:/Users/Gary/source/repos/HardwareTester/instance/app.db
# SQLALCHEMY_DATABASE_URI=sqlite:///C:/Users/Gary/source/repos/HardwareTester/instance/app.db
SQLALCHEMY_DATABASE_URI=postgresql://postgres:postgres/instance/pgapp.db
DATABASE_URL=postgresql://postgres:postgres/instance/pgapp.db  # Replace with your database URL
SQLALCHEMY_TRACK_MODIFICATIONS=False

# Network settings
HOST=127.0.0.1
PORT=5000

# MQTT configuration
MQTT_BROKER=test.mosquitto.org
MQTT_PORT=1883
MQTT_USERNAME=  # Optional: Provide username if required
MQTT_PASSWORD=  # Optional: Provide password if required
MQTT_TLS=False  # Use True for secure MQTT connections

# Logging
LOG_LEVEL=DEBUG  # Use INFO or WARNING in production
LOG_FILE=app.log

# File upload settings
UPLOAD_FOLDER=uploads
BLUEPRINT_UPLOAD_FOLDER=blueprints/upload
MAX_CONTENT_LENGTH=16777216  # 16 MB
ALLOWED_SPEC_SHEET_EXTENSIONS=pdf,docx,xlsx
ALLOWED_TEST_PLAN_EXTENSIONS=pdf,csv,txt

# Other settings
DEFAULT_SERIAL_PORT=COM3  # Default serial port for communication
DEFAULT_BAUDRATE=9600  # Default baud rate for serial communication

# Security settings
SESSION_COOKIE_SECURE=False  # Set to True in production
REMEMBER_COOKIE_SECURE=False  # Set to True in production
