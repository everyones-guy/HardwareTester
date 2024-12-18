from flask import Flask, jsonify
from HardwareTester.config import config
from HardwareTester.extensions import db, migrate, socketio, csrf, login_manager
from HardwareTester.views import register_blueprints
from HardwareTester.models import User
from HardwareTester.views.configuration_views import config_bp
from HardwareTester.views.auth_views import auth_bp
import logging


def create_app(config_name="default"):
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if config_name == "development" else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Log to console
            logging.FileHandler("hardware_tester.log"),  # Log to file
        ],
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Initializing app with config: {config_name}")

    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # Replace with actual login route if applicable

    # Register blueprints
    register_blueprints(app)
    app.register_blueprint(config_bp)  # Register configuration blueprint
    app.register_blueprint(auth_bp)  # Register authentication blueprint

    # Register error handlers
    register_error_handlers(app)

    logger.info("App initialized successfully")

    # User loader callback
    @login_manager.user_loader
    def load_user(user_id):
        logger.debug(f"Loading user with ID: {user_id}")
        return User.query.get(int(user_id))

    return app


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
