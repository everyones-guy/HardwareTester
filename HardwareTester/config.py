import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

def str_to_bool(value):
    """Convert string values to boolean."""
    return str(value).strip().lower() in ("true", "yes", "1")

class Config:
    """Base configuration with default settings."""
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_DIR = os.getenv("INSTANCE_DIR", "instance")
    UPLOAD_ROOT = os.getenv("UPLOAD_FOLDER", "uploads")  # Base upload folder from .env\
    

    os.makedirs(INSTANCE_DIR, exist_ok=True)  # Ensure the instance directory exists

    # Flask settings
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_CONFIG = os.getenv("FLASK_CONFIG", "development")

    # Network settings
    HOST = os.getenv("HOST", "localhost")
    PORT = int(os.getenv("PORT", 5000))

    # Debugging and Logging
    DEBUG = str_to_bool(os.getenv("DEBUG", "True"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", os.path.join(BASE_DIR, "app.log"))

    # Database settings
    #SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(INSTANCE_DIR, 'app.db')}")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/hardware_tester")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload settings
   # UPLOAD_ROOT = os.getenv("UPLOAD_ROOT")
    UPLOAD_BLUEPRINTS_FOLDER = os.getenv("UPLOAD_BLUEPRINTS_FOLDER", "blueprints")
    UPLOAD_CONFIGS_FOLDER = os.getenv("UPLOAD_CONFIGS_FOLDER", "configs")
    UPLOAD_MODIFIED_JSON_FILES = os.getenv("UPLOAD_MODIFIED_JSON_FILES", "modified_json_files")
    
    os.makedirs(UPLOAD_BLUEPRINTS_FOLDER, exist_ok=True)
    os.makedirs(UPLOAD_CONFIGS_FOLDER, exist_ok=True)
    os.makedirs(UPLOAD_MODIFIED_JSON_FILES, exist_ok=True)

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # Default 16 MB
    ALLOWED_SPEC_SHEET_EXTENSIONS = set(os.getenv("ALLOWED_SPEC_SHEET_EXTENSIONS", "pdf,docx,xlsx").split(","))
    ALLOWED_TEST_PLAN_EXTENSIONS = set(os.getenv("ALLOWED_TEST_PLAN_EXTENSIONS", "pdf,csv,txt").split(","))

    # Serial communication settings
    DEFAULT_SERIAL_PORT = os.getenv("DEFAULT_SERIAL_PORT", "COM3")
    DEFAULT_BAUDRATE = int(os.getenv("DEFAULT_BAUDRATE", 115200))

    # Base URL
    BASE_URL = os.getenv("BASE_URL", "localhost:5000")
    SECURE_BASE_URL = os.getenv("SECURE_BASE_URL", "https://localhost:5000")

    # MQTT settings
    MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    MQTT_USERNAME = os.getenv("MQTT_USERNAME", None)
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", None)
    MQTT_TLS = str_to_bool(os.getenv("MQTT_TLS", "False"))

    # Security
    SESSION_COOKIE_SECURE = str_to_bool(os.getenv("SESSION_COOKIE_SECURE", "False"))
    REMEMBER_COOKIE_SECURE = str_to_bool(os.getenv("REMEMBER_COOKIE_SECURE", "False"))

class DevelopmentConfig(Config):
    """Development configuration with debug enabled."""
    DEBUG = True
    ENV = "development"
    LOGIN_DISABLED = True

class TestingConfig(Config):
    """Testing configuration with a separate test database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/tst_hardware_tester")
    WTF_CSRF_ENABLED = False  # Disable CSRF for easier testing
    LOG_LEVEL = "WARNING"
    ENV = "testing"
    LOGIN_DISABLED = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = "ERROR"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", Config.SQLALCHEMY_DATABASE_URI)
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    ENV = "production"

    # Ensure secure configurations
    if Config.SECRET_KEY == "default-secret-key":
        raise ValueError("A secure SECRET_KEY must be set for production.")

# Environment-based configuration mapping
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
