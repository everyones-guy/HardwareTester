# system_status_views

from flask import Blueprint, jsonify, render_template
from flask_login import login_required
from HardwareTester.services.system_status_service import SystemStatusService
from HardwareTester.extensions import logger
#from HardwareTester.utils.custom_logger import CustomLogger

# Initialize logger
#logger = CustomLogger.get_logger("system_status_views")

system_status_bp = Blueprint("system_status", __name__, url_prefix="/system-status")


@system_status_bp.route("/", methods=["GET"])
@login_required
def system_status_page():
    """Render the system status dashboard."""
    logger.info("Rendering system status dashboard page.")
    return render_template("system_status.html")


@system_status_bp.route("/summary", methods=["GET"])
@login_required
def system_status_summary():
    """Get system status summary."""
    logger.info("Fetching system status summary.")
    try:
        status = SystemStatusService.get_full_system_status()
        if status["success"]:
            logger.info("System status summary fetched successfully.")
            return jsonify(status)
        logger.warning(f"Failed to fetch system status summary: {status['error']}")
        return jsonify({"success": False, "error": status["error"]}), 500
    except Exception as e:
        logger.error(f"Unexpected error fetching system status summary: {e}")
        return jsonify({"success": False, "error": "Failed to fetch system status summary."}), 500


@system_status_bp.route("/metrics", methods=["GET"])
@login_required
def system_status_metrics():
    """Get detailed system metrics."""
    logger.info("Fetching detailed system metrics.")
    try:
        metrics = SystemStatusService.get_detailed_metrics()
        if metrics["success"]:
            logger.info("Detailed system metrics fetched successfully.")
            return jsonify(metrics)
        logger.warning(f"Failed to fetch detailed system metrics: {metrics['error']}")
        return jsonify({"success": False, "error": metrics["error"]}), 500
    except Exception as e:
        logger.error(f"Unexpected error fetching detailed system metrics: {e}")
        return jsonify({"success": False, "error": "Failed to fetch detailed system metrics."}), 500
