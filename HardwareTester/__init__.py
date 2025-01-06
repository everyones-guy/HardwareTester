from flask import Flask, jsonify
from HardwareTester.config import config
from HardwareTester.extensions import db, socketio, migrate, csrf, login_manager, ma
from HardwareTester.views import register_blueprints
from HardwareTester.models import User
from HardwareTester.utils.bcrypt_utils import bcrypt
import logging

def create_app(config_name="default"):
    logging.basicConfig(
        level=logging.DEBUG if config_name == "development" else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("hardware_tester.log")],
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Initializing app with config: {config_name}")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")
    csrf.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Register blueprints and error handlers
    register_blueprints(app)
    register_error_handlers(app)

    logger.info("App initialized successfully")

    @login_manager.user_loader
    def load_user(user_id):
        from HardwareTester.models.user_models import User
        return db.User.query.get(int(user_id))

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
    
