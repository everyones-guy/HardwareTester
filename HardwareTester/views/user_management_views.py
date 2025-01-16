from flask import Blueprint, request, jsonify, render_template, abort
from flask_login import current_user
from HardwareTester.services.user_management_service import UserManagementService

user_management_bp = Blueprint("user_management", __name__)

@user_management_bp.route("/users", methods=["GET"])
def manage_users():
    """Render the user management page."""
    if current_user.role != 'user':  # Restrict access to admin users
        abort(403)
    return render_template("user_management.html")


@user_management_bp.route("/users/list", methods=["GET"])
def list_users_endpoint():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    response = UserManagementService.list_users(page, per_page)
    return jsonify(response)


@user_management_bp.route("/users/add", methods=["POST"])
def add_user_endpoint():
    """Add a new user."""
    if current_user.role != 'user':  # Restrict access
        abort(403)
    data = request.json
    response = UserManagementService.create_user(data["username"], data["email"], data["password"])
    return jsonify(response)


@user_management_bp.route("/users/update/<int:user_id>", methods=["POST"])
def update_user_endpoint(user_id):
    """Update user details."""
    if current_user.role != 'user':  # Restrict access
        abort(403)
    data = request.json
    response = UserManagementService.update_user(
        user_id,
        username=data.get("username"),
        email=data.get("email"),
        password=data.get("password"),
    )
    return jsonify(response)


@user_management_bp.route("/users/delete/<int:user_id>", methods=["DELETE"])
def delete_user_endpoint(user_id):
    """Delete a user."""
    if current_user.role != 'user':  # Restrict access
        abort(403)
    response = UserManagementService.delete_user(user_id)
    return jsonify(response)
