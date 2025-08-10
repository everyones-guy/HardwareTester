import os
import platform
import socket
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

def get_local_ip():
    """Dynamically fetch local IP (useful in WSL/Windows setups)"""
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "127.0.0.1"

def str_to_bool(value):
    return str(value).strip().lower() in ("true", "yes", "1")

# Base dynamic root setup
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
IS_WSL = "microsoft" in platform.uname().release.lower()

DEFAULT_UPLOAD_ROOT = (
    os.path.join(PROJECT_ROOT, "uploads") if IS_WSL
    else os.path.expanduser("~/HardwareTester/uploads")
)

UPLOAD_ROOT = os.getenv("UPLOAD_ROOT", DEFAULT_UPLOAD_ROOT)

# Ensure these folders exist
def ensure_dirs_exist(*paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)

class Config:
    BASE_DIR = PROJECT_ROOT
    INSTANCE_DIR = os.getenv("INSTANCE_DIR", os.path.join(BASE_DIR, "instance"))
    os.makedirs(INSTANCE_DIR, exist_ok=True)

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_CONFIG = os.getenv("FLASK_CONFIG", "development")

    # Networking
    HOST_IP = os.getenv("HOST_IP", get_local_ip())
    HOST = HOST_IP
    PORT = int(os.getenv("PORT", 5000))

    # Logging
    DEBUG = str_to_bool(os.getenv("DEBUG", "True"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", os.path.join(BASE_DIR, "app.log"))

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"postgresql+psycopg2://postgres:postgres@{HOST_IP}:5432/hardware_tester"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload paths
    UPLOAD_ROOT = UPLOAD_ROOT
    UPLOAD_BLUEPRINTS_FOLDER = os.path.join(UPLOAD_ROOT, "blueprints")
    UPLOAD_CONFIGS_FOLDER = os.path.join(UPLOAD_ROOT, "configs")
    UPLOAD_MODIFIED_JSON_FILES = os.path.join(UPLOAD_ROOT, "modified_json_files")

    ensure_dirs_exist(
        UPLOAD_ROOT,
        UPLOAD_BLUEPRINTS_FOLDER,
        UPLOAD_CONFIGS_FOLDER,
        UPLOAD_MODIFIED_JSON_FILES,
    )

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    ALLOWED_SPEC_SHEET_EXTENSIONS = set(os.getenv("ALLOWED_SPEC_SHEET_EXTENSIONS", "pdf,docx,xlsx").split(","))
    ALLOWED_TEST_PLAN_EXTENSIONS = set(os.getenv("ALLOWED_TEST_PLAN_EXTENSIONS", "pdf,csv,txt").split(","))

    # Serial
    DEFAULT_SERIAL_PORT = os.getenv("DEFAULT_SERIAL_PORT", "COM3")
    DEFAULT_BAUDRATE = int(os.getenv("DEFAULT_BAUDRATE", 115200))

    # URLs
    BASE_URL = f"http://{HOST}:{PORT}"
    SECURE_BASE_URL = f"https://{HOST}:{PORT}"

    # MQTT
    MQTT_BROKER = os.getenv("MQTT_BROKER", HOST)
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    MQTT_USERNAME = os.getenv("MQTT_USERNAME")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
    MQTT_TLS = str_to_bool(os.getenv("MQTT_TLS", "False"))

    # Security
    SESSION_COOKIE_SECURE = str_to_bool(os.getenv("SESSION_COOKIE_SECURE", "False"))
    REMEMBER_COOKIE_SECURE = str_to_bool(os.getenv("REMEMBER_COOKIE_SECURE", "False"))

class DevelopmentConfig(Config):
    DEBUG = True
    ENV = "development"
    LOGIN_DISABLED = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"postgresql+psycopg2://postgres:postgres@{Config.HOST}:5432/hardware_tester"
    )
    WTF_CSRF_ENABLED = False
    LOG_LEVEL = "WARNING"
    ENV = "testing"
    LOGIN_DISABLED = True

class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = "ERROR"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", Config.SQLALCHEMY_DATABASE_URI)
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    ENV = "production"

    if Config.SECRET_KEY == "default-secret-key":
        raise ValueError("A secure SECRET_KEY must be set for production.")

config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
