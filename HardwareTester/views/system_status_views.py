
from flask import Blueprint, jsonify, render_template
from HardwareTester.services.system_status_service import fetch_system_status, get_detailed_metrics

system_status_bp = Blueprint("system_status", __name__, url_prefix="/system-status")


@system_status_bp.route("/", methods=["GET"])
def system_status_page():
    """Render the system status dashboard."""
    return render_template("system_status.html")


@system_status_bp.route("/summary", methods=["GET"])
def system_status_summary():
    """Get system status summary."""
    status = fetch_system_status()
    if status["success"]:
        return jsonify(status)
    return jsonify({"success": False, "error": status["error"]})


@system_status_bp.route("/metrics", methods=["GET"])
def system_status_metrics():
    """Get detailed system metrics."""
    metrics = get_detailed_metrics()
    if metrics["success"]:
        return jsonify(metrics)
    return jsonify({"success": False, "error": metrics["error"]})

