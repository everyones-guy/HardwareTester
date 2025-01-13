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

# Configure global logger
logger = logging.getLogger("HardwareTester", log_file="logs/hardware_tester.log", level="INFO")
logger.setLevel(logging.INFO)

# File handler with rotation
file_handler = RotatingFileHandler("logs/app.log", maxBytes=5 * 1024 * 1024, backupCount=5)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
console_handler.setLevel(logging.INFO)

# Customize LoginManager settings
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Log initialization status
try:
    logger.info("Extensions initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing extensions: {e}")
    raise e


