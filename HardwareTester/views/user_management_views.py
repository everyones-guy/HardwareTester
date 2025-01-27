from flask import Blueprint, request, jsonify, render_template, abort
from flask_login import login_required, current_user
from HardwareTester.services.user_management_service import UserManagementService
from HardwareTester.extensions import logger

user_management_bp = Blueprint("user_management", __name__, url_prefix="/users")

@user_management_bp.route("/", methods=["GET"])
@login_required
def manage_users():
    """Render the user management page."""
    if current_user.role != 'user':  # Restrict access to admin users
        logger.info("User not authorized to access user management")
        abort(403)
    return render_template("user_management.html")


@user_management_bp.route("/list", methods=["GET"])
@login_required
def list_users_endpoint():
    """List all users."""
    logger.info("Listing all users")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    response = UserManagementService.list_users(page, per_page)
    return jsonify(response)


@user_management_bp.route("/add", methods=["POST"])
@login_required
def add_user_endpoint():
    """Add a new user."""
    if current_user.role != 'user':  # Restrict access
        logger.error("User not authorized to add a new user")
        abort(403)
    data = request.json
    response = UserManagementService.create_user(data["username"], data["email"], data["password"])
    return jsonify(response)


@user_management_bp.route("/update/<int:user_id>", methods=["POST"])
@login_required
def update_user_endpoint(user_id):
    """Update user details."""
    if current_user.role != 'user':  # Restrict access
        logger.error("User not authorized to update user details")
        abort(403)
    data = request.json
    response = UserManagementService.update_user(
        user_id,
        username=data.get("username"),
        email=data.get("email"),
        password=data.get("password"),
    )
    return jsonify(response)


@user_management_bp.route("/delete/<int:user_id>", methods=["DELETE"])
@login_required
def delete_user_endpoint(user_id):
    """Delete a user."""
    if current_user.role != 'user':  # Restrict access
        logger.error("User not authorized to delete a user")
        abort(403)
    response = UserManagementService.delete_user(user_id)
    return jsonify(response)
