from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required
from Hardware_Tester_App.services.valve_service import (
    get_all_valves,
    add_valve,
    delete_valve,
    update_valve,
    get_valve_status,
    change_valve_state  # Import new state-changing function
)
from Hardware_Tester_App.extensions import logger

logger.info("Valve_views")

valve_bp = Blueprint("valve", __name__)

@valve_bp.route("/valves", methods=["GET"])
@login_required
def show_valves():
    """Render the valve management page."""
    return render_template("valve_management.html")

@valve_bp.route("/api/valves/list", methods=["GET"])
@login_required
def list_valves():
    """Get a list of all valves."""
    response = get_all_valves()
    return jsonify(response)

@valve_bp.route("/api/valves/add", methods=["POST"])
@login_required
def add_new_valve():
    """Add a new valve."""
    data = request.json
    response = add_valve(data)
    return jsonify(response)

@valve_bp.route("/api/valves/<int:valve_id>/delete", methods=["DELETE"])
@login_required
def delete_existing_valve(valve_id):
    """Delete a valve."""
    response = delete_valve(valve_id)
    return jsonify(response)

@valve_bp.route("/api/valves/<int:valve_id>/update", methods=["PUT"])
@login_required
def update_existing_valve(valve_id):
    """Update valve details."""
    data = request.json
    response = update_valve(valve_id, data)
    return jsonify(response)

@valve_bp.route("/api/valves/<int:valve_id>/status", methods=["GET"])
@login_required
def valve_status(valve_id):
    """Get the status of a specific valve."""
    response = get_valve_status(valve_id)
    return jsonify(response)

@valve_bp.route("/api/valves/<int:valve_id>/change-state", methods=["POST"])
@login_required
def change_valve_state_endpoint(valve_id):
    """
    Change the state of a specific valve.
    States can be: open, closed, faulty, maintenance.
    """
    data = request.json
    new_state = data.get("state")
    if not new_state:
        logger.error("Missing 'state' field in request body")
        return jsonify({"success": False, "error": "Missing 'state' field in request body"}), 400

    response = change_valve_state(valve_id, new_state)
    return jsonify(response)
