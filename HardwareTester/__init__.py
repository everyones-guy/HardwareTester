from flask import Flask, jsonify
from HardwareTester.config import config
from HardwareTester.extensions import db, socketio, migrate, csrf, login_manager, ma, logger
from HardwareTester.views import register_blueprints
from HardwareTester.utils.bcrypt_utils import bcrypt
from HardwareTester.models.user_models import User
import logging

def create_app(config_name="default"):
    """
    Create and configure the Flask application.
    :param config_name: The configuration name ('development', 'testing', or 'production').
    :return: Configured Flask application instance.
    """
    # Configure logging
    configure_logging(config_name)
    logger.info(f"Initializing app with config: {config_name}")

    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    initialize_extensions(app)

    # Register blueprints and error handlers
    register_blueprints(app)
    register_error_handlers(app)

    logger.info("App initialized successfully")

    @login_manager.user_loader
    def load_user(user_id):
        """
        Load a user by ID for Flask-Login.
        :param user_id: User ID from the session.
        :return: User instance or None.
        """
        logger.debug(f"Loading user with ID: {user_id}")
        return User.query.get(int(user_id))

    return app


def initialize_extensions(app):
    """
    Initialize Flask extensions.
    :param app: Flask application instance.
    """
    try:
        db.init_app(app)
        migrate.init_app(app, db)
        socketio.init_app(app, cors_allowed_origins="*")
        csrf.init_app(app)
        bcrypt.init_app(app)
        ma.init_app(app)
        login_manager.init_app(app)
        login_manager.login_view = "auth.login"
        logger.info("Extensions initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing extensions: {e}")
        raise e


def configure_logging(config_name):
    """
    Configure application logging based on the environment.
    :param config_name: The configuration name ('development', 'testing', or 'production').
    """
    level = logging.DEBUG if config_name == "development" else logging.INFO
    logging.basicConfig(
        level=level,
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
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 error: {error}")
        return jsonify({"error": "An internal error occurred"}), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        logger.warning(f"403 error: {error}")
        return jsonify({"error": "Forbidden"}), 403

    @app.errorhandler(401)
    def unauthorized_error(error):
        logger.warning(f"401 error: {error}")
        return jsonify({"error": "Unauthorized"}), 401
