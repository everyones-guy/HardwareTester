import os

class Config:
    """Base configuration with default settings."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "default-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
    ALLOWED_SPEC_SHEET_EXTENSIONS = {"pdf", "docx", "xlsx"}
    ALLOWED_TEST_PLAN_EXTENSIONS = {"pdf", "csv", "txt"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB upload limit
    BASE_URL = os.environ.get("BASE_URL", " http://127.0.0.1:5000")  # Default value if not set


    # Add logging for better observability
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.environ.get("LOG_FILE", "app.log")


class DevelopmentConfig(Config):
    """Development configuration with debug enabled."""
    DEBUG = True
    ENV = "development"


class TestingConfig(Config):
    """Testing configuration with a separate test database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"
    WTF_CSRF_ENABLED = False  # Disable CSRF for easier testing
    ENV = "testing"


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///prod.db")
    ENV = "production"

    # Ensure secure cookies and sessions
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


# Mapping for environment-based configurations
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
