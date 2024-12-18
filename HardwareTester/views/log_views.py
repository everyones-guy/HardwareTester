from flask import Blueprint, jsonify
from HardwareTester.services.log_service import get_log_history, stream_logs

log_bp = Blueprint("log", __name__)

@log_bp.route("/history", methods=["GET"])
def fetch_logs():
    """Fetch log history."""
    logs = get_log_history()
    return jsonify({"logs": logs})

@log_bp.route("/stream", methods=["GET"])
def stream_log_view():
    """Stream real-time logs."""
    return stream_logs()
