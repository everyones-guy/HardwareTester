import logging
from logging.handlers import RotatingFileHandler
import os


class CustomLogger:
    """Utility for creating and managing custom loggers."""

    loggers = {}  # Cache loggers to prevent duplicates

    @staticmethod
    def get_logger(name: str, log_file="logs/app.log", level="INFO", per_module=False) -> logging.Logger:
        """
        Retrieve or create a logger by name.
        :param name: Name of the logger.
        :param log_file: Path to the default log file.
        :param level: Logging level (e.g., INFO, DEBUG).
        :param per_module: If True, creates a separate log file for this module.
        :return: Configured `logging.Logger` instance.
        """
        # Determine log file path for per-module logging
        if per_module:
            module_name = name.lower().replace(" ", "_")
            log_file = f"logs/{module_name}.log"

        # Check if logger already exists in the cache
        if name in CustomLogger.loggers:
            return CustomLogger.loggers[name]

        # Create logger and configure it
        logger = logging.getLogger(name)

        if not logger.handlers:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

            # File handler with rotation
            file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
            file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            file_handler.setLevel(level)

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            console_handler.setLevel(level)

            # Add handlers to the logger
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

            # Set the logger level
            logger.setLevel(level)

        # Cache the logger
        CustomLogger.loggers[name] = logger
        return logger
