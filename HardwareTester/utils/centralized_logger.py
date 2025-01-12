import logging
from logging.handlers import RotatingFileHandler
import os

class CentralizedLogger:
    """Centralized logger configuration for HardwareTester."""

    LOG_LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    @staticmethod
    def get_logger(name: str, log_file="logs/app.log", level="INFO") -> logging.Logger:
        """
        Initialize and return a logger instance.
        :param name: Name of the logger (usually the module name).
        :param log_file: Path to the log file.
        :param level: Logging level (e.g., INFO, DEBUG).
        :return: Configured logger instance.
        """
        logger = logging.getLogger(name)
        if not logger.handlers:  # Avoid duplicate handlers
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

            # File handler with rotation
            file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
            file_handler.setFormatter(logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            file_handler.setLevel(CentralizedLogger.LOG_LEVELS.get(level.upper(), logging.INFO))

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            console_handler.setLevel(CentralizedLogger.LOG_LEVELS.get(level.upper(), logging.INFO))

            # Add handlers to the logger
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            logger.setLevel(CentralizedLogger.LOG_LEVELS.get(level.upper(), logging.INFO))

        return logger
