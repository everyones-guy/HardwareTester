
from flask import Blueprint, jsonify, request
from HardwareTester.services.peripherals_service import PeripheralsService

peripherals_bp = Blueprint("peripherals", __name__)

@peripherals_bp.route("/peripherals/list", methods=["GET"])
def list_peripherals():
    """List all peripherals."""
    result = PeripheralsService.list_peripherals()
    if result["success"]:
        return jsonify(result), 200
    return jsonify({"error": result["error"]}), 500

@peripherals_bp.route("/peripherals/add", methods=["POST"])
def add_peripheral():
    """Add a new peripheral."""
    data = request.json
    name = data.get("name")
    properties = data.get("properties", {})
    if not name:
        return jsonify({"error": "Name is required."}), 400

    result = PeripheralsService.add_peripheral(name, properties)
    if result["success"]:
        return jsonify(result), 201
    return jsonify({"error": result["error"]}), 500

@peripherals_bp.route("/peripherals/delete/<int:peripheral_id>", methods=["DELETE"])
def delete_peripheral(peripheral_id):
    """Delete a peripheral by ID."""
    result = PeripheralsService.delete_peripheral(peripheral_id)
    if result["success"]:
        return jsonify(result), 200
    return jsonify({"error": result["error"]}), 404

@peripherals_bp.route("/peripherals/update/<int:peripheral_id>", methods=["PUT"])
def update_peripheral(peripheral_id):
    """Update a peripheral."""
    data = request.json
    properties = data.get("properties", {})

    result = PeripheralsService.update_peripheral(peripheral_id, properties)
    if result["success"]:
        return jsonify(result), 200
    return jsonify({"error": result["error"]}), 404

