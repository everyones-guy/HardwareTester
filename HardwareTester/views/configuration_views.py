
from flask import Blueprint, render_template, request, jsonify
from HardwareTester.services.configuration_service import save_configuration, load_configuration

configuration_bp = Blueprint("configurations", __name__)

@configuration_bp.route("/", methods=["GET"])
def configuration_management():
    """Render the Configuration Management page."""
    return render_template("configuration_management.html")

@configuration_bp.route("/save", methods=["POST"])
def save_config():
    """Save a new configuration."""
    data = request.json
    result = save_configuration(data)
    if result["success"]:
        return jsonify({"success": True, "message": "Configuration saved successfully."})
    return jsonify({"success": False, "error": result["error"]}), 500

@configuration_bp.route("/load", methods=["GET"])
def load_config():
    """Load saved configurations."""
    result = load_configuration()
    if result["success"]:
        return jsonify({"success": True, "configurations": result["data"]})
    return jsonify({"success": False, "error": result["error"]}), 500

