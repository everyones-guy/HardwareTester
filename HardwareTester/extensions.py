import logging
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_marshmallow import Marshmallow

# Set up logging
logger = logging.getLogger(__name__)

# Initialize extensions
try:
    db = SQLAlchemy()
    socketio = SocketIO(cors_allowed_origins="*")  # Allow CORS
    migrate = Migrate()
    csrf = CSRFProtect()
    login_manager = LoginManager()
    ma = Marshmallow()

    # Customize LoginManager settings
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    logger.info("Extensions initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing extensions: {e}")
    raise e
