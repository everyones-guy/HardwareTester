import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

def str_to_bool(value):
    return str(value).strip().lower() in ("true", "yes", "1")


class Config:
    """Base configuration with default settings."""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SECRET_KEY = os.environ.get("SECRET_KEY", "default-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    ALLOWED_SPEC_SHEET_EXTENSIONS = set(
        os.getenv("ALLOWED_SPEC_SHEET_EXTENSIONS", "pdf,docx,xlsx").split(",")
    )
    ALLOWED_TEST_PLAN_EXTENSIONS = set(
        os.getenv("ALLOWED_TEST_PLAN_EXTENSIONS", "pdf,csv,txt").split(",")
    )
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB upload limit
    DEFAULT_SERIAL_PORT = os.getenv("DEFAULT_SERIAL_PORT", "COM3")
    DEFAULT_BAUDRATE = int(os.getenv("DEFAULT_BAUDRATE", 9600))
    BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5000")
    MQTT_BROKER = os.environ.get("MQTT_BROKER", "test.mosquitto.org")
    MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
    MQTT_USERNAME = os.environ.get("MQTT_USERNAME")
    MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")
    MQTT_TLS = str_to_bool(os.environ.get("MQTT_TLS", "False"))

    # Logging configuration
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.environ.get("LOG_FILE", "app.log")


class DevelopmentConfig(Config):
    """Development configuration with debug enabled."""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    ENV = "development"


class TestingConfig(Config):
    """Testing configuration with a separate test database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"
    WTF_CSRF_ENABLED = False  # Disable CSRF for easier testing
    LOG_LEVEL = "WARNING"
    ENV = "testing"


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///prod.db")
    SECRET_KEY = os.environ.get("SECRET_KEY", "default-secret-key")
    LOG_LEVEL = "ERROR"
    ENV = "production"

    # Ensure secure cookies and sessions
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL must be set for production.")
    if SECRET_KEY == "default-secret-key":
        raise ValueError("A secure SECRET_KEY must be set for production.")


# Mapping for environment-based configurations
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
