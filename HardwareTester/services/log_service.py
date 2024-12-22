import os
import logging
from flask_socketio import emit
from flask import jsonify

# Logger setup
LOG_FILE = "hardware_tester.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # Also logs to console
    ]
)

logger = logging.getLogger("HardwareTester")

def add_log_entry(level, message):
    """
    Add a log entry with the specified level and message.
    """
    if level.lower() == "info":
        logger.info(message)
    elif level.lower() == "warning":
        logger.warning(message)
    elif level.lower() == "error":
        logger.error(message)
    elif level.lower() == "debug":
        logger.debug(message)
    else:
        logger.info(message)  # Default to info if level is invalid

    # Emit the log to the UI via Socket.IO
    emit("log_update", {"level": level.upper(), "message": message}, broadcast=True)

    return {"success": True, "message": "Log added successfully."}

def fetch_logs():
    """
    Fetch logs from the log file.
    """
    if not os.path.exists(LOG_FILE):
        return {"success": False, "error": "Log file does not exist."}

    with open(LOG_FILE, "r") as log_file:
        logs = log_file.readlines()
    return {"success": True, "logs": logs}
