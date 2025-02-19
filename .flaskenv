# .flaskenv

# Flask environment settings
FLASK_APP=HardwareTester:create_app  # Entry point for the Flask app
FLASK_ENV=development
FLASK_CONFIG=development
FLASK_DEBUG=1  # Set to 0 in production
# TEMPLATES_FOLDER=C:/Users/Gary/source/repos/HardwareTester/HardwareTester/templates

# Database Configuration
# DATABASE_URL=mysql:///instance/app.db  # mysql database example
# SQLALCHEMY_DATABASE_URI=sqlite:///instance/app.db # SQLite database example
# INSTANCE_DIR=C:/Users/Gary/source/repos/HardwareTester/HardwareTester/instance
# DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/hardware_tester
# SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://postgres:postgres@localhost:5432/hardware_tester
# SQLALCHEMY_TRACK_MODIFICATIONS=FalseINSTANCE_DIR=C:/Users/Gary/source/repos/HardwareTester/HardwareTester/instance
DATABASE_URL=postgresql+psycopg2://postgres:postgres@172.17.128.1:5432/hardware_tester
SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://postgres:postgres@172.17.128.1:5432/hardware_tester
SQLALCHEMY_TRACK_MODIFICATIONS=False

# Network settings
HOST=172.17.128.1
PORT=5000
BASE_URL=http://172.17.128.1:5000
SECURE_BASE_URL=https://172.17.128.1:5000
BASE_API_URL=http://172.17.128.1:5000/api

# MQTT configuration
MQTT_BROKER=172.17.128.1
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TLS=False

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=app.log

# File Upload Settings
UPLOAD_ROOT=c:/Users/Gary/source/repos/HardwareTester/HardwareTester/uploads
UPLOAD_FOLDER=c:/Users/Gary/source/repos/HardwareTester/HardwareTester/uploads
UPLOAD_BLUEPRINTS_FOLDER=c:/Users/Gary/source/repos/HardwareTester/HardwareTester/uploads/blueprints
UPLOAD_CONFIGS_FOLDER=c:/Users/Gary/source/repos/HardwareTester/HardwareTester/uploads/configs
UPLOAD_MODIFIED_JSON_FILES=c:/Users/Gary/source/repos/HardwareTester/HardwareTester/uploads/modified_json_files

#UPLOAD_BLUEPRINTS_FOLDER=blueprints
#UPLOAD_CONFIGS_FOLDER=configs
#UPLOAD_MODIFIED_JSON_FILES=modified_json_files
# 16 MB limit
MAX_CONTENT_LENGTH=16777216
    
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
