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

# Load environment variables from .env
load_dotenv()

# Initialize logger
logger = logging.getLogger("app")

# Ensure the migration object is initialized
migrate = Migrate()

def create_app(config_name="default", *args, **kwargs):
    """ven
    Create and configure the Flask application.
    :param config_name: The configuration name ('development', 'testing', or 'production').
    :return: Configured Flask application instance.
    """

    # Initialize Flask app
    #app = Flask(__name__)
    app = Flask(__name__, static_folder="./emulator-dashboard-1/build", static_url_path="/")

    #CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
    CORS(app, resources={r"/api/*": {"origins": "*"}})  # Allow all


    # Ensure we always get a valid class reference, NOT a string
    config_class = config.get(config_name, config["default"])
    app.config.from_object(config_class)

    # Initialize extensions
    initialize_extensions(app)

    # Register CLI commands
    register_cli_commands(app)

    # Register blueprints and error handlers
    register_blueprints(app)
    register_error_handlers(app)

    # Serve React app
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_react(path):
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, "index.html")


    # Ensure upload folders are created
    ensure_upload_folders(app)

    @app.context_processor
    def inject_context():
        """Inject variables available globally to templates."""
        csrf_token = get_token(current_user.id) if current_user.is_authenticated else None
        return {
            "now": datetime.utcnow(),
            "csrf_token": csrf_token,
        }

    logger.info("App initialized successfully.")
    return app



def initialize_extensions(app):
    """
    Initialize Flask extensions.
    :param app: Flask application instance.
    """
    try:
        db.init_app(app)
        migrate.init_app(app, db)
        socketio.init_app(app)
        csrf.init_app(app)
        ma.init_app(app)
        login_manager.init_app(app)
        bcrypt.init_app(app)

        # LoginManager configurations
        login_manager.login_view = "auth.login"
        login_manager.login_message = "Please log in to access this page."
        login_manager.login_message_category = "warning"

        logger.info("Extensions initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing extensions: {e}")
        raise e


import logging

def configure_logging(config_name):
    log_level = logging.DEBUG if config_name == "development" else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("hardware_tester.log"),
        ],
    )
    logging.getLogger("werkzeug").setLevel(logging.WARNING)  # Suppress Werkzeug logs



def register_error_handlers(app):
    """
    Register error handlers for the Flask application.
    :param app: Flask application instance.
    """
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


# ----------------------
# CLI Registration
# ----------------------
def register_cli_commands(app):
    """Register CLI commands with the Flask app."""
    from Hardware_Tester_App.cli import cli

    app.cli.add_command(cli)
    logger.info("CLI commands registered successfully.")


@login_manager.user_loader
def load_user(user_id):
    """
    Load a user by ID for Flask-Login.
    :param user_id: User ID from the session.
    :return: User instance or None.
    """
    try:
        logger.debug(f"Loading user with ID: {user_id}")
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Error loading user with ID {user_id}: {e}")
        return None


def ensure_upload_folders(app):
    """Ensure all required upload folders exist."""
    # upload_folder_root = app.config.get('UPLOAD_FOLDER_ROOT', 'uploads')
    upload_folder_root = os.path.abspath(app.config.get('UPLOAD_FOLDER_ROOT', 'uploads'))

    
    # Define subfolders for different purposes
    subfolders = ['blueprints', 'configs', 'logs', 'data']

    for subfolder in subfolders:
        folder_path = os.path.join(upload_folder_root, subfolder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            app.logger.info(f"Created directory: {folder_path}")