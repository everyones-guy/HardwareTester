from HardwareTester.extensions import logger

class LoggerUtils:
    """Utility methods for structured logging."""

    @staticmethod
    def log_debug(message):
        logger.debug(message)

    @staticmethod
    def log_info(message):
        logger.info(message)

    @staticmethod
    def log_warning(message):
        logger.warning(message)

    @staticmethod
    def log_error(message):
        logger.error(message)

    @staticmethod
    def log_critical(message):
        logger.critical(message)
