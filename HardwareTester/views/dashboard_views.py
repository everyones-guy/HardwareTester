
from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from HardwareTester.services.dashboard_service import DashboardService

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/", methods=["GET"])
@login_required
def dashboard_home():
    """Render the dashboard homepage."""
    return render_template("dashboard.html")


@dashboard_bp.route("/data", methods=["GET"])
@login_required
def get_dashboard_data():
    """Fetch dashboard data for the current user."""
    result = DashboardService.get_dashboard_data(user_id=current_user.id)
    if result["success"]:
        return jsonify({"success": True, "data": result["data"]})
    return jsonify({"success": False, "error": result["error"]})


@dashboard_bp.route("/create", methods=["POST"])
@login_required
def create_dashboard_item():
    """Create a new dashboard item."""
    title = request.form.get("title")
    description = request.form.get("description")
    if not title:
        return jsonify({"success": False, "error": "Title is required"})

    result = DashboardService.create_dashboard_item(
        user_id=current_user.id, title=title, description=description
    )
    return jsonify(result)


@dashboard_bp.route("/update/<int:item_id>", methods=["POST"])
@login_required
def update_dashboard_item(item_id):
    """Update an existing dashboard item."""
    title = request.form.get("title")
    description = request.form.get("description")
    result = DashboardService.update_dashboard_item(
        item_id=item_id, title=title, description=description
    )
    return jsonify(result)


@dashboard_bp.route("/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_dashboard_item(item_id):
    """Delete a dashboard item."""
    result = DashboardService.delete_dashboard_item(item_id=item_id)
    return jsonify(result)

