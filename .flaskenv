# .flaskenv

# Flask environment settings
# Entry point for the Flask app
FLASK_APP=Hardware_Tester_App:create_app
FLASK_ENV=development
FLASK_CONFIG=development
# Set to 0 in production
FLASK_DEBUG=1
# TEMPLATES_FOLDER=C:/Users/Gary/source/repos/HardwareTester/Hardware_Tester_App/templates

# Database Configuration
# DATABASE_URL=mysql:///instance/app.db  # mysql database example
# SQLALCHEMY_DATABASE_URI=sqlite:///instance/app.db # SQLite database example
# INSTANCE_DIR=C:/Users/Gary/source/repos/HardwareTester/Hardware_Tester_App/instance
# DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/hardware_tester
# SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://postgres:postgres@localhost:5432/hardware_tester
# SQLALCHEMY_TRACK_MODIFICATIONS=FalseINSTANCE_DIR=C:/Users/Gary/source/repos/HardwareTester/Hardware_Tester_App/instance
# DATABASE_URL=postgresql+psycopg2://postgres:postgres@172.17.128.1:5432/hardware_tester
# SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://postgres:postgres@172.17.128.1:5432/hardware_tester
DATABASE_URL=postgresql+psycopg2://postgres:postgres@${HOST_IP:-127.0.0.1}:5432/hardware_tester
SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://postgres:postgres@${HOST_IP:-127.0.0.1}:5432/hardware_tester
SQLALCHEMY_TRACK_MODIFICATIONS=False

# Network settings
HOST=${HOST:-127.0.0.1}
PORT=5000
# BASE_URL=http://172.17.128.1:5000
# SECURE_BASE_URL=https://172.17.128.1:5000
# BASE_API_URL=http://172.17.128.1:5000/api
BASE_URL=http://127.0.0.1:${PORT}
SECURE_BASE_URL=https://127.0.0.1:${PORT}
BASE_API_URL=http://127.0.0.1:5000/api

# MQTT configuration
MQTT_BROKER=${HOST_IP:-127.0.0.1}
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TLS=False

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=app.log

# File Upload Settings
UPLOAD_ROOT=/mnt/c/Users/Gary/source/repos/HardwareTester/Hardware_Tester_App/uploads
UPLOAD_FOLDER=/mnt/c/Users/Gary/source/repos/HardwareTester/Hardware_Tester_App/uploads
UPLOAD_BLUEPRINTS_FOLDER=/mnt/c/Users/Gary/source/repos/HardwareTester/Hardware_Tester_App/uploads/blueprints
UPLOAD_CONFIGS_FOLDER=/mnt/c/Users/Gary/source/repos/HardwareTester/Hardware_Tester_App/uploads/configs
UPLOAD_MODIFIED_JSON_FILES=/mnt/c/Users/Gary/source/repos/HardwareTester/Hardware_Tester_App/uploads/modified_json_files

#UPLOAD_BLUEPRINTS_FOLDER=blueprints
#UPLOAD_CONFIGS_FOLDER=configs
#UPLOAD_MODIFIED_JSON_FILES=modified_json_files
# 16 MB limit
MAX_CONTENT_LENGTH=16777216
    
#UPLOAD_FOLDER=uploads
#BLUEPRINT_UPLOAD_FOLDER=blueprints
#UPLOAD_FOLDER_ROOT=C:/Users/Gary/source/repos/HardwareTester/Hardware_Tester_App/uploads
ALLOWED_SPEC_SHEET_EXTENSIONS=pdf,docx,xlsx
ALLOWED_TEST_PLAN_EXTENSIONS=pdf,csv,txt

# Other settings
# Default serial port for communication
DEFAULT_SERIAL_PORT=COM3
# Default baud rate for serial communication
DEFAULT_BAUDRATE=115200

# Security settings
# Set to True in production
SESSION_COOKIE_SECURE=False  
# Set to True in production
REMEMBER_COOKIE_SECURE=False  
