
from flask import Blueprint, jsonify, render_template, request
from HardwareTester.services.valve_service import (
    get_all_valves,
    add_valve,
    delete_valve,
    update_valve,
    get_valve_status
)

valve_bp = Blueprint("valve", __name__, url_prefix="/valves")

@valve_bp.route("/", methods=["GET"])
def show_valves():
    """Render the valve management page."""
    return render_template("valve_management.html")

@valve_bp.route("/list", methods=["GET"])
def list_valves():
    """Get a list of all valves."""
    response = get_all_valves()
    return jsonify(response)

@valve_bp.route("/add", methods=["POST"])
def add_new_valve():
    """Add a new valve."""
    data = request.json
    response = add_valve(data)
    return jsonify(response)

@valve_bp.route("/<int:valve_id>/delete", methods=["DELETE"])
def delete_existing_valve(valve_id):
    """Delete a valve."""
    response = delete_valve(valve_id)
    return jsonify(response)

@valve_bp.route("/<int:valve_id>/update", methods=["PUT"])
def update_existing_valve(valve_id):
    """Update valve details."""
    data = request.json
    response = update_valve(valve_id, data)
    return jsonify(response)

@valve_bp.route("/<int:valve_id>/status", methods=["GET"])
def valve_status(valve_id):
    """Get the status of a specific valve."""
    response = get_valve_status(valve_id)
    return jsonify(response)
