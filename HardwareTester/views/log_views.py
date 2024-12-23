from flask import Blueprint, jsonify, request
from HardwareTester.services.log_service import get_log_history, stream_logs
from HardwareTester.services.log_service import LogService


log_bp = Blueprint("log", __name__)

@log_bp.route("/", methods=["GET"])
def get_logs():
    """Fetch logs with optional filters."""
    level = request.args.get("level", "ALL")
    keyword = request.args.get("keyword")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    
    logs = LogService.get_logs(level=level, keyword=keyword, start_date=start_date, end_date=end_date)
    return jsonify(logs)

@log_bp.route("/history", methods=["GET"])
def fetch_logs():
    """Fetch log history."""
    logs = get_log_history()
    return jsonify({"logs": logs})

@log_bp.route("/stream", methods=["GET"])
def stream_log_view():
    """Stream real-time logs."""
    return stream_logs()
