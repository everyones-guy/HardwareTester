# .flaskenv

# Flask environment settings
FLASK_APP=HardwareTester:create_app  # Entry point for the Flask app
FLASK_ENV=development
FLASK_CONFIG=development
FLASK_DEBUG=1  # Set to 0 in production
# TEMPLATES_FOLDER=C:/Users/Gary/source/repos/HardwareTester/HardwareTester/templates

# Database Configuration
# DATABASE_URL=mysql:///instance/app.db  # Default SQLite database location
# SQLALCHEMY_DATABASE_URI=sqlite:///instance/app.db
INSTANCE_DIR=C:/Users/Gary/source/repos/HardwareTester/HardwareTester
DATABASE_URL=sqlite:///C:/Users/Gary/source/repos/HardwareTester/HardwareTester/instance/app.db
SQLALCHEMY_DATABASE_URI=sqlite:///C:/Users/Gary/source/repos/HardwareTester/HardwareTester/instance/app.db
SQLALCHEMY_TRACK_MODIFICATIONS=False

# Network settings
HOST=localhost
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

# File Upload Settings
UPLOAD_ROOT=c:/Users/Gary/source/repos/HardwareTester/HardwareTester/uploads
UPLOAD_FOLDER=uploads
UPLOAD_BLUEPRINTS_FOLDER=blueprints
UPLOAD_CONFIGS_FOLDER=configs
UPLOAD_MODIFIED_JSON_FILES=modified_json_files
MAX_CONTENT_LENGTH=16777216  # 16 MB
    
#UPLOAD_FOLDER=uploads
#BLUEPRINT_UPLOAD_FOLDER=blueprints
#UPLOAD_FOLDER_ROOT=C:/Users/Gary/source/repos/HardwareTester/HardwareTester/uploads
ALLOWED_SPEC_SHEET_EXTENSIONS=pdf,docx,xlsx
ALLOWED_TEST_PLAN_EXTENSIONS=pdf,csv,txt

# Other settings
DEFAULT_SERIAL_PORT=COM3  # Default serial port for communication
DEFAULT_BAUDRATE=115200  # Default baud rate for serial communication

# Security settings
SESSION_COOKIE_SECURE=False  # Set to True in production
REMEMBER_COOKIE_SECURE=False  # Set to True in production
