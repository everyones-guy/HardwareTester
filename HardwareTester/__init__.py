from flask import Flask, jsonify, render_template, request
from HardwareTester.config import config
from HardwareTester.extensions import db, socketio, migrate, csrf, login_manager, ma, bcrypt
from HardwareTester.views import register_blueprints
from HardwareTester.models.user_models import User
from HardwareTester.utils.custom_logger import CustomLogger
from datetime import datetime
from cli import register_commands

# Initialize logger
logger = CustomLogger.get_logger("app")

def create_app(config_name="default"):
    """
    Create and configure the Flask application.
    :param config_name: The configuration name ('development', 'testing', or 'production').
    :return: Configured Flask application instance.
    """

    # Initialize Flask app
    app = Flask(__name__)
    app.config['LOGIN_DISABLED'] = False
    app.config.from_object(config[config_name])

    # Initialize extensions
    initialize_extensions(app)

    # Register CLI commands
    register_commands(app)

    # Register blueprints and error handlers
    register_blueprints(app)
    register_error_handlers(app)


    @app.context_processor
    def inject_now():
        return {"now": datetime.utcnow()}

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


def configure_logging(config_name):
    """
    Configure application logging based on the environment.
    :param config_name: The configuration name ('development', 'testing', or 'production').
    """
    level = logger.debug if config_name == "development" else logger.info
    logger.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logger.StreamHandler(),
            logger.FileHandler("hardware_tester.log"),
        ],
    )
    logger.getLogger("werkzeug").setLevel(logger.WARNING)  # Suppress Werkzeug logs


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


#def register_cli_commands(app):
#    """
#    Register CLI commands with the Flask app.
#    :param app: Flask application instance.
#    """
#    app.cli.register_commands(cli)
#    logger.info("CLI commands registered successfully.")


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

