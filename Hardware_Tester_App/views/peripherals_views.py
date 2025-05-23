from flask import Blueprint, jsonify, request, render_template
from flask_login import current_user, login_required
from Hardware_Tester_App.services.peripherals_service import PeripheralsService
from Hardware_Tester_App.models.user_models import UserRole

peripherals_bp = Blueprint("peripherals", __name__)

@peripherals_bp.route("/peripherals", methods=["GET"])
@login_required
def dashboard():
    """Render the peripherals dashboard."""
    if current_user.role not in [UserRole.ADMIN.value, UserRole.USER.value]:
        return render_template("error.html", message="Access denied")
    return render_template("peripherals.html")

@peripherals_bp.route("/api/peripherals/list", methods=["GET"])
@login_required
def list_peripherals():
    """List all peripherals."""
    result = PeripheralsService.list_peripherals()
    if result["success"]:
        return jsonify(result), 200
    return jsonify({"error": result["error"]}), 500

@peripherals_bp.route("/api/peripherals/add", methods=["POST"])
@login_required
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

@peripherals_bp.route("/api/peripherals/delete/<int:peripheral_id>", methods=["DELETE"])
@login_required
def delete_peripheral(peripheral_id):
    """Delete a peripheral by ID."""
    result = PeripheralsService.delete_peripheral(peripheral_id)
    if result["success"]:
        return jsonify(result), 200
    return jsonify({"error": result["error"]}), 404

@peripherals_bp.route("/api/peripherals/update/<int:peripheral_id>", methods=["PUT"])
@login_required
def update_peripheral(peripheral_id):
    """Update a peripheral."""
    data = request.json
    properties = data.get("properties", {})

    result = PeripheralsService.update_peripheral(peripheral_id, properties)
    if result["success"]:
        return jsonify(result), 200
    return jsonify({"error": result["error"]}), 404
