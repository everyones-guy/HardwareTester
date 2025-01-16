from HardwareTester.utils.custom_logger import CustomLogger
import os


def test_logger_creation():
    """Test if logger initializes correctly."""
    log_file = "logs/test_logger.log"
    logger = CustomLogger.get_logger("TestLogger")
    assert os.path.exists(log_file)

def test_logging_levels():
    """Test logging at different verbosity levels."""
    logger = CustomLogger.get_logger("TestLogger")
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning.")
    logger.error("This is an error.")
    logger.critical("This is critical.")
    # Manually verify the log file content if necessary
