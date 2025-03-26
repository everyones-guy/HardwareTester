
from flask import Blueprint, request, jsonify
from HardwareTester.services.blueprint_service import BlueprintService

blueprint_bp = Blueprint("blueprint", __name__)

@blueprint_bp.route("/api/blueprint/generate_blueprint", methods=["POST"])
def generate_blueprint():
    """Generate a hardware blueprint for a given machine."""
    machine_address = request.json.get("machine_address")
    
    if not machine_address:
        return jsonify({"error": "Machine address is required"}), 400

    blueprint_data = BlueprintService.scan_machine(machine_address)
    
    if "error" in blueprint_data:
        return jsonify({"error": blueprint_data["error"]}), 500
    
    return jsonify({"success": True, "blueprint": blueprint_data}), 200
