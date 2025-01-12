import logging
from logging.handlers import RotatingFileHandler
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt

import os

# Initialize extensions
db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
ma = Marshmallow()
bcrypt = Bcrypt()

# Customize LoginManager settings
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"

# Configure global logger
def initialize_logger(name="HardwareTester", log_file="logs/app.log", level=logging.INFO):
    """
    Initialize and configure a logger with file and console handlers.
    :param name: Logger name.
    :param log_file: Path to the log file.
    :param level: Logging level.
    :return: Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:  # Avoid duplicate handlers
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # File handler with rotation
        file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        file_handler.setLevel(level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        console_handler.setLevel(level)

        # Add handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(level)

    return logger

# Configure global logger
logger = initialize_logger()

# Log initialization status
try:
    logger.info("Extensions initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing extensions: {e}")
    raise e


