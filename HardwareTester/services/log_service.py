
import os
from datetime import datetime
from HardwareTester.utils.logger import Logger

logger = Logger(name="LogService", log_file="logs/log_service.log", level="INFO")

# Directory to store logs
LOG_DIRECTORY = "logs"

class LogService:
    """A service for managing logs."""
    
    @staticmethod
    def get_logs(level="ALL", keyword=None, start_date=None, end_date=None):
        """Retrieve filtered logs."""
        logs = []

        try:
            with open("app.log", "r") as log_file:
                for line in log_file:
                    if LogService.filter_log(line, level, keyword, start_date, end_date):
                        logs.append(LogService.parse_log_line(line))
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            return {"success": False, "error": str(e)}

        return {"success": True, "logs": logs}

    @staticmethod
    def filter_log(line, level, keyword, start_date, end_date):
        """Filter log line by level, keyword, and date range."""
        if level != "ALL" and level not in line:
            return False
        if keyword and keyword.lower() not in line.lower():
            return False
        if start_date or end_date:
            timestamp = line.split()[0]
            log_date = datetime.strptime(timestamp, "%Y-%m-%d").date()
            if start_date and log_date < datetime.strptime(start_date, "%Y-%m-%d").date():
                return False
            if end_date and log_date > datetime.strptime(end_date, "%Y-%m-%d").date():
                return False
        return True

    @staticmethod
    def parse_log_line(line):
        """Parse a single log line into a structured dictionary."""
        parts = line.split(" ", 3)
        return {
            "timestamp": parts[0],
            "level": parts[1],
            "message": parts[3].strip() if len(parts) > 3 else "",
        }

    @staticmethod
    def list_log_files():
        """List all log files in the log directory."""
        try:
            files = os.listdir(LOG_DIRECTORY)
            log_files = [f for f in files if f.endswith(".log")]
            logger.info(f"Listed {len(log_files)} log files.")
            return {"success": True, "log_files": log_files}
        except Exception as e:
            logger.error(f"Error listing log files: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def fetch_log_file(file_name):
        """Fetch the content of a specific log file."""
        try:
            file_path = os.path.join(LOG_DIRECTORY, file_name)
            if not os.path.exists(file_path):
                logger.warning(f"Log file {file_name} does not exist.")
                return {"success": False, "error": "Log file does not exist."}

            with open(file_path, "r") as file:
                content = file.readlines()
            logger.info(f"Fetched content of log file: {file_name}")
            return {"success": True, "content": content}
        except Exception as e:
            logger.error(f"Error fetching log file {file_name}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete_log_file(file_name):
        """Delete a specific log file."""
        try:
            file_path = os.path.join(LOG_DIRECTORY, file_name)
            if not os.path.exists(file_path):
                logger.warning(f"Log file {file_name} does not exist.")
                return {"success": False, "error": "Log file does not exist."}

            os.remove(file_path)
            logger.info(f"Deleted log file: {file_name}")
            return {"success": True, "message": f"Log file {file_name} deleted successfully."}
        except Exception as e:
            logger.error(f"Error deleting log file {file_name}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def clear_all_logs():
        """Delete all log files."""
        try:
            files = os.listdir(LOG_DIRECTORY)
            log_files = [f for f in files if f.endswith(".log")]

            for log_file in log_files:
                os.remove(os.path.join(LOG_DIRECTORY, log_file))

            logger.info("Cleared all log files.")
            return {"success": True, "message": "All log files cleared."}
        except Exception as e:
            logger.error(f"Error clearing all log files: {e}")
            return {"success": False, "error": str(e)}

