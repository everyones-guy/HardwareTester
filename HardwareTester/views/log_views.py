from flask import Blueprint, jsonify, request, render_template
from HardwareTester.services.log_service import LogService
from HardwareTester.utils.custom_logger import CustomLogger

# Initialize logger
logger = CustomLogger.get_logger("log_views")

logs_bp = Blueprint("logs", __name__, url_prefix="/logs")

@logs_bp.route("/", methods=["GET"])
def logs():
    """Fetch and filter logs from the log file or database."""
    import os
    from datetime import datetime

    log_file_path = "logs/app.log"  # Replace with the actual path to your log file
    logs = []

    try:
        # Check if log file exists
        if os.path.exists(log_file_path):
            with open(log_file_path, "r") as log_file:
                for line in log_file:
                    # Assuming logs are stored in a format like: [LEVEL] [TIMESTAMP] MESSAGE
                    parts = line.split(" ", 2)
                    if len(parts) == 3:
                        level = parts[0].strip("[]")
                        timestamp = parts[1].strip("[]")
                        message = parts[2].strip()

                        # Validate timestamp format (optional)
                        try:
                            datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                        except ValueError:
                            continue

                        logs.append({"level": level, "timestamp": timestamp, "message": message})

        # Apply filters
        level = request.args.get("level")
        if level and level != "ALL":
            logs = [log for log in logs if log["level"] == level]

        return jsonify({"success": True, "logs": logs})
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to fetch logs: {str(e)}"})


@logs_bp.route("/recent", methods=["GET"])
def recent_logs():
    # Mock logs for testing
    logs = [
        "[INFO] Application started",
        "[DEBUG] Debugging mode enabled",
        "[ERROR] Error encountered during operation"
    ]
    return jsonify({"success": True, "logs": logs})


# Activity Logs
@logs_bp.route("/activity", methods=["GET"])
def get_activity_logs():
    """Get activity logs with optional filters."""
    user_id = request.args.get("user_id", type=int)
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    result = LogService.get_activity_logs(user_id=user_id, start_date=start_date, end_date=end_date)
    return jsonify(result), 200 if result["success"] else 500


@logs_bp.route("/activity/log", methods=["POST"])
def log_activity():
    """Log a new activity."""
    data = request.get_json()
    user_id = data.get("user_id")
    action = data.get("action")
    if not user_id or not action:
        return jsonify({"success": False, "error": "user_id and action are required."}), 400
    result = LogService.log_activity(user_id=user_id, action=action)
    return jsonify(result), 200 if result["success"] else 500


# Notifications
@logs_bp.route("/notifications", methods=["GET"])
def get_notifications():
    """Get notifications with optional filters."""
    user_id = request.args.get("user_id", type=int)
    only_unread = request.args.get("only_unread", default=False, type=bool)
    result = LogService.get_notifications(user_id=user_id, only_unread=only_unread)
    return jsonify(result), 200 if result["success"] else 500


@logs_bp.route("/notifications/send", methods=["POST"])
def send_notification():
    """Send a notification."""
    data = request.get_json()
    message = data.get("message")
    user_id = data.get("user_id")
    if not message:
        return jsonify({"success": False, "error": "message is required."}), 400
    result = LogService.send_notification(message=message, user_id=user_id)
    return jsonify(result), 200 if result["success"] else 500


@logs_bp.route("/notifications/read/<int:notification_id>", methods=["POST"])
def mark_notification_as_read(notification_id):
    """Mark a notification as read."""
    result = LogService.mark_notification_as_read(notification_id)
    return jsonify(result), 200 if result["success"] else 404
