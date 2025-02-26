from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required
from HardwareTester.services.controller_service import (
    get_all_controllers,
    add_controller,
    delete_controller,
    update_controller,
    get_controller_status,
    change_controller_state  # Import new state-changing function
)
from HardwareTester.extensions import logger

logger.info("Controller_Views")

controller_bp = Blueprint("controller", __name__)

@controller_bp.route("/controllers", methods=["GET"])
@login_required
def show_controllers():
    """Render the controller management page."""
    return render_template("controller_management.html")

@controller_bp.route("/api/controllers/list", methods=["GET"])
@login_required
def list_controllers():
    """Get a list of all controllers."""
    response = get_all_controllers()
    return jsonify(response)

@controller_bp.route("/api/controllers/add", methods=["POST"])
@login_required
def add_new_controller():
    """Add a new controller."""
    data = request.json
    response = add_controller(data)
    return jsonify(response)

@controller_bp.route("/api/controllers/<int:controller_id>/delete", methods=["DELETE"])
@login_required
def delete_existing_controller(controller_id):
    """Delete a controller."""
    response = delete_controller(controller_id)
    return jsonify(response)

@controller_bp.route("/api/controllers/<int:controller_id>/update", methods=["PUT"])
@login_required
def update_existing_controller(controller_id):
    """Update controller details."""
    data = request.json
    response = update_controller(controller_id, data)
    return jsonify(response)

@controller_bp.route("/api/controllers/<int:controller_id>/status", methods=["GET"])
@login_required
def controller_status(controller_id):
    """Get the status of a specific controller."""
    response = get_controller_status(controller_id)
    return jsonify(response)

@controller_bp.route("/api/controllers/<int:controller_id>/change-state", methods=["POST"])
@login_required
def change_controller_state_endpoint(controller_id):
    """
    Change the state of a specific controller.
    States can be: open, closed, faulty, maintenance.
    """
    data = request.json
    new_state = data.get("state")
    if not new_state:
        logger.error("Missing 'state' field in request body")
        return jsonify({"success": False, "error": "Missing 'state' field in request body"}), 400

    response = change_controller_state(controller_id, new_state)
    return jsonify(response)
