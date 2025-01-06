# extensions.py
# contains the initialization of Flask extensions used in the application.

import logging
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_marshmallow import Marshmallow

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# StreamHandler ensures logs are visible in the console
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(console_handler)

# Initialize extensions
db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")  # Allow CORS for Socket.IO
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
ma = Marshmallow()

# Customize LoginManager settings
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"

# Log initialization status
try:
    logger.info("Extensions initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing extensions: {e}")
    raise e
