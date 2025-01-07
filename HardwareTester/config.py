import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

def str_to_bool(value):
    """Convert string values to boolean."""
    return str(value).strip().lower() in ("true", "yes", "1")

class Config:
    """Base configuration with default settings."""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
    os.makedirs(INSTANCE_DIR, exist_ok=True)  # Ensure the instance directory exists

    # Flask settings
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_CONFIG = os.getenv("FLASK_CONFIG", "development")

    # Network settings
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 5000))

    # Debugging and Logging
    DEBUG = str_to_bool(os.getenv("DEBUG", "True"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "app.log")

    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{INSTANCE_DIR}/app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload settings
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # Default 16 MB
    ALLOWED_SPEC_SHEET_EXTENSIONS = set(os.getenv("ALLOWED_SPEC_SHEET_EXTENSIONS", "pdf,docx,xlsx").split(","))
    ALLOWED_TEST_PLAN_EXTENSIONS = set(os.getenv("ALLOWED_TEST_PLAN_EXTENSIONS", "pdf,csv,txt").split(","))

    # Serial communication settings
    DEFAULT_SERIAL_PORT = os.getenv("DEFAULT_SERIAL_PORT", "COM3")
    DEFAULT_BAUDRATE = int(os.getenv("DEFAULT_BAUDRATE", 9600))

    # Base URL
    BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")

    # MQTT settings
    MQTT_BROKER = os.getenv("MQTT_BROKER", "test.mosquitto.org")
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

class TestingConfig(Config):
    """Testing configuration with a separate test database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///instance/test.db"
    WTF_CSRF_ENABLED = False  # Disable CSRF for easier testing
    LOG_LEVEL = "WARNING"
    ENV = "testing"

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = "ERROR"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{Config.INSTANCE_DIR}/prod.db")
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    ENV = "production"

    # Ensure secure configurations
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL must be set for production.")
    if Config.SECRET_KEY == "default-secret-key":
        raise ValueError("A secure SECRET_KEY must be set for production.")

# Environment-based configuration mapping
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
