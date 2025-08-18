from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_migrate import Migrate
from flask_login import current_user
from flask_cors import CORS
from datetime import datetime

import os
import logging
from dotenv import load_dotenv

from .config import config
from .extensions import db, socketio, migrate, csrf, login_manager, ma, bcrypt
from .views import register_blueprints
from .models.user_models import User
from .utils.token_utils import get_token
from .diagnostics import log_routes

# Load environment variables early
load_dotenv()

logger = logging.getLogger("app")

def create_app(config_name="default", *args, **kwargs):
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder="../frontend/build", static_url_path="/")
    app.url_map.strict_slashes = False

    # Load configuration class from the config mapping
    config_class = config.get(config_name, config["default"])
    app.config.from_object(config_class)

    # Enable CORS for API routes
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Initialize all extensions
    initialize_extensions(app)

    # Register CLI commands
    register_cli_commands(app)

    # Register Flask Blueprints and error handlers
    register_blueprints(app)
    register_error_handlers(app)

    # Log the routs - turn this off during prod
    log_routes(app)

    # Serve React frontend (from /frontend/build)
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_react(path):
        target_path = os.path.join(app.static_folder, path)
        if path and os.path.exists(target_path):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, "index.html")

    # Ensure necessary folders exist
    ensure_upload_folders(app)

    # Inject CSRF and timestamp into templates
    @app.context_processor
    def inject_context():
        csrf_token = get_token(current_user.id) if current_user.is_authenticated else None
        return {
            "now": datetime.utcnow(),
            "csrf_token": csrf_token,
        }

    logger.info("App initialized successfully.")
    return app


def initialize_extensions(app):
    """Initialize Flask extensions."""
    try:
        db.init_app(app)
        migrate.init_app(app, db)
        socketio.init_app(app)
        csrf.init_app(app)
        ma.init_app(app)
        login_manager.init_app(app)
        bcrypt.init_app(app)

        login_manager.login_view = "auth.login"
        login_manager.login_message = "Please log in to access this page."
        login_manager.login_message_category = "warning"

        logger.info("Extensions initialized successfully.")
    except Exception as e:
        logger.error(f"Extension initialization failed: {e}")
        raise e


def register_cli_commands(app):
    """Attach custom CLI command groups (like db, emulator, mqtt, etc)."""
    from . import cli
    app.cli.add_command(cli.cli)
    logger.info("CLI commands registered.")


def register_error_handlers(app):
    """Register error handlers for common HTTP errors."""
    @app.errorhandler(404)
    def not_found_error(error):
        logger.warning(f"404 error: {error}")
        if request.accept_mimetypes["application/json"]:
            return jsonify({"error": "Resource not found"}), 404
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 error: {error}")
        if request.accept_mimetypes["application/json"]:
            return jsonify({"error": "An internal error occurred"}), 500
        return render_template("500.html"), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        logger.warning(f"403 error: {error}")
        if request.accept_mimetypes["application/json"]:
            return jsonify({"error": "Forbidden"}), 403
        return render_template("403.html"), 403

    @app.errorhandler(401)
    def unauthorized_error(error):
        logger.warning(f"401 error: {error}")
        if request.accept_mimetypes["application/json"]:
            return jsonify({"error": "Unauthorized"}), 401
        return render_template("401.html"), 401


@login_manager.user_loader
def load_user(user_id):
    """Load a user by ID for Flask-Login."""
    try:
        logger.debug(f"Loading user with ID: {user_id}")
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Error loading user with ID {user_id}: {e}")
        return None


def ensure_upload_folders(app):
    """Ensure all expected upload-related subfolders exist."""
    root = os.path.abspath(app.config.get("UPLOAD_FOLDER_ROOT", "uploads"))
    subfolders = ["blueprints", "configs", "logs", "data"]

    for folder in subfolders:
        path = os.path.join(root, folder)
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f"Created missing directory: {path}")
