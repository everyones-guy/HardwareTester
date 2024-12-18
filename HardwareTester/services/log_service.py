import os
from datetime import datetime

def get_log_history(log_file="logs/application.log"):
    """
    Fetch log history from a specified log file.
    :param log_file: Path to the log file.
    :return: Log contents or an error message.
    """
    try:
        if not os.path.exists(log_file):
            return {"success": False, "error": f"Log file '{log_file}' not found."}

        with open(log_file, "r") as f:
            logs = f.readlines()
        return {"success": True, "logs": logs}

    except Exception as e:
        return {"success": False, "error": str(e)}


def stream_logs(log_file="logs/application.log"):
    """
    Simulate real-time log streaming.
    :param log_file: Path to the log file.
    :return: Generator for real-time logs.
    """
    try:
        with open(log_file, "r") as f:
            # Move to the end of the file
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if line:
                    yield {"timestamp": datetime.now().isoformat(), "message": line.strip()}
    except Exception as e:
        yield {"timestamp": datetime.now().isoformat(), "error": str(e)}
