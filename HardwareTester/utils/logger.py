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

    @staticmethod
    def _get_formatter():
        """Return a formatter with a consistent log format."""
        return logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    @staticmethod
    def getLogger(name: str, log_file="logs/app.log", level="INFO") -> logging.Logger:
        """
        Retrieve or create a logger by name.
        :param name: Name of the logger.
        :param log_file: Path to the log file.
        :param level: Logging level (e.g., INFO, DEBUG).
        :return: The `logging.Logger` instance.
        """
        logger = logging.getLogger(name)

        # Configure the logger if it hasn't been set up yet
        if not logger.handlers:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

            # File handler with rotation
            file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
            file_handler.setFormatter(Logger._get_formatter())
            file_handler.setLevel(Logger.LOG_LEVELS.get(level.upper(), logging.INFO))

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(Logger._get_formatter())
            console_handler.setLevel(Logger.LOG_LEVELS.get(level.upper(), logging.INFO))

            # Add handlers to the logger
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

            # Set the logger level
            logger.setLevel(Logger.LOG_LEVELS.get(level.upper(), logging.INFO))

        return logger


# Utility function for Flask integration
def init_flask_logging(app, level="INFO"):
    """Integrate logging into a Flask application."""
    logger = Logger.getLogger(name="FlaskApp", log_file="logs/flask_app.log", level=level)
    app.logger.handlers = logger.handlers
    app.logger.setLevel(logger.level)
