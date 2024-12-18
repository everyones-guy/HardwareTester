from flask import Blueprint, jsonify, request
from HardwareTester.services.configuration_service import save_configuration, load_configuration, list_configurations

config_bp = Blueprint("configurations", __name__, url_prefix="/configurations")

@config_bp.route("/", methods=["POST"])
def save_config():
    """Save a configuration layout."""
    data = request.json
    name = data.get("name")
    layout = data.get("layout")

    if not name or not layout:
        return jsonify({"success": False, "message": "Name and layout are required."}), 400

    result = save_configuration(name, layout)
    if result["success"]:
        return jsonify({"success": True, "message": result["message"]})
    return jsonify({"success": False, "error": result["error"]}), 500

@config_bp.route("/", methods=["GET"])
def list_configs():
    """List all configurations."""
    result = list_configurations()
    if result["success"]:
        return jsonify({"success": True, "configurations": result["configurations"]})
    return jsonify({"success": False, "error": result["error"]}), 500

@config_bp.route("/<int:config_id>", methods=["GET"])
def get_config(config_id):
    """Load a specific configuration."""
    result = load_configuration(config_id)
    if result["success"]:
        return jsonify({"success": True, "configuration": result["configuration"]})
    return jsonify({"success": False, "error": result["error"]}), 404

