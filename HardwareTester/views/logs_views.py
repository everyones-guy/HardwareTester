
from flask import Blueprint, jsonify, request
from HardwareTester.services.log_service import LogService

logs_bp = Blueprint("logs", __name__)

@logs_bp.route("/logs/list", methods=["GET"])
def list_logs():
    """List all available log files."""
    result = LogService.list_log_files()
    if result["success"]:
        return jsonify(result), 200
    return jsonify({"error": result["error"]}), 500


@logs_bp.route("/logs/view/<file_name>", methods=["GET"])
def view_log(file_name):
    """View the content of a specific log file."""
    result = LogService.fetch_log_file(file_name)
    if result["success"]:
        return jsonify(result), 200
    return jsonify({"error": result["error"]}), 404


@logs_bp.route("/logs/delete/<file_name>", methods=["DELETE"])
def delete_log(file_name):
    """Delete a specific log file."""
    result = LogService.delete_log_file(file_name)
    if result["success"]:
        return jsonify(result), 200
    return jsonify({"error": result["error"]}), 404


@logs_bp.route("/logs/clear", methods=["DELETE"])
def clear_logs():
    """Clear all log files."""
    result = LogService.clear_all_logs()
    if result["success"]:
        return jsonify(result), 200
    return jsonify({"error": result["error"]}), 500

