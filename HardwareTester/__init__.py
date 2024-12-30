from flask import Flask, jsonify
from HardwareTester import config
from HardwareTester.extensions import db, migrate, socketio, csrf, login_manager
from HardwareTester.views import register_blueprints
from HardwareTester.models import User
from HardwareTester.utils.db_utils import initialize_database  # Ensure this exists
from HardwareTester.views.configuration_views import configuration_bp
from HardwareTester.views.auth_views import auth_bp
import logging


def create_app(config_name=None):
    """Application factory to create a Flask app."""
    # Determine config dynamically if not provided
    config_name = config_name or "default"

    # Configure logging
    configure_logging(config_name)

    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Initialize database
    with app.app_context():
        initialize_database(app)

    # Register blueprints
    register_blueprints(app)
    app.register_blueprint(configuration_bp)
    app.register_blueprint(auth_bp)

    # Register error handlers
    register_error_handlers(app)

    logging.info("App initialized successfully")

    # User loader callback
    @login_manager.user_loader
    def load_user(user_id):
        logging.debug(f"Loading user with ID: {user_id}")
        return User.query.get(int(user_id))

    return app


def configure_logging(config_name):
    """Configure logging based on environment."""
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
    """Register custom error handlers."""
    @app.errorhandler(404)
    def not_found_error(error):
        logging.warning(f"404 error: {error}")
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logging.error(f"500 error: {error}")
        return jsonify({"error": "An internal error occurred"}), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        logging.warning(f"403 error: {error}")
        return jsonify({"error": "Forbidden"}), 403

    @app.errorhandler(401)
    def unauthorized_error(error):
        logging.warning(f"401 error: {error}")
        return jsonify({"error": "Unauthorized"}), 401
