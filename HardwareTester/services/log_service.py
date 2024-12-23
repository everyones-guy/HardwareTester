from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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
