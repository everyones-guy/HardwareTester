import logging
from logging.handlers import RotatingFileHandler
import os

class Logger:
    """Custom logging library for HardwareTester."""

    LOG_LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    def __init__(self, name="HardwareTester", log_file="logs/app.log", level="INFO"):
        """Initialize the logger."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.LOG_LEVELS.get(level.upper(), logging.INFO))

        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # File handler with rotation
        file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
        file_handler.setFormatter(self._get_formatter())
        file_handler.setLevel(self.LOG_LEVELS.get(level.upper(), logging.INFO))

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self._get_formatter())
        console_handler.setLevel(self.LOG_LEVELS.get(level.upper(), logging.INFO))

        # Add handlers to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _get_formatter(self):
        """Return a formatter with a consistent log format."""
        return logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def set_level(self, level):
        """Dynamically adjust the log level."""
        level = self.LOG_LEVELS.get(level.upper(), logging.INFO)
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)


# Utility function for Flask integration
def init_flask_logging(app, level="INFO"):
    """Integrate logging into a Flask application."""
    logger = Logger(name="FlaskApp", log_file="logs/flask_app.log", level=level)
    app.logger.handlers = logger.logger.handlers
    app.logger.setLevel(logger.logger.level)
