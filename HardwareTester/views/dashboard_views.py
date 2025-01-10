from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from HardwareTester.services.dashboard_service import DashboardService
from HardwareTester.models.user_models import UserRole

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/", methods=["GET"])
#@login_required
def dashboard_home():
    """Render the dashboard homepage."""
    if current_user.role not in [UserRole.ADMIN.value, UserRole.USER.value]:
        #return render_template("error.html", message="Access denied")
        return render_template("dashboard.html", message="Had To Do it")
    return render_template("dashboard.html")


@dashboard_bp.route("/data", methods=["GET"])
#@login_required
def get_dashboard_data():
    """Fetch dashboard data for the current user."""
    if current_user.role not in [UserRole.ADMIN.value, UserRole.USER.value]:
        return jsonify({"success": False, "error": "Access denied"})

    result = DashboardService.get_dashboard_data(user_id=current_user.id)
    if result["success"]:
        return jsonify({"success": True, "data": result["data"]})
    return jsonify({"success": False, "error": result["error"]})


@dashboard_bp.route("/create", methods=["POST"])
# @login_required
def create_dashboard_item():
    """Create a new dashboard item."""
    if current_user.role != UserRole.ADMIN.value:
        return jsonify({"success": False, "error": "Access denied"})

    title = request.form.get("title")
    description = request.form.get("description")
    if not title:
        return jsonify({"success": False, "error": "Title is required"})

    result = DashboardService.create_dashboard_item(
        user_id=current_user.id, title=title, description=description
    )
    return jsonify(result)


@dashboard_bp.route("/update/<int:item_id>", methods=["POST"])
# @login_required
def update_dashboard_item(item_id):
    """Update an existing dashboard item."""
    if current_user.role != UserRole.ADMIN.value:
        return jsonify({"success": False, "error": "Access denied"})

    title = request.form.get("title")
    description = request.form.get("description")
    result = DashboardService.update_dashboard_item(
        item_id=item_id, title=title, description=description
    )
    return jsonify(result)


@dashboard_bp.route("/delete/<int:item_id>", methods=["POST"])
# @login_required
def delete_dashboard_item(item_id):
    """Delete a dashboard item."""
    if current_user.role != UserRole.ADMIN.value:
        return jsonify({"success": False, "error": "Access denied"})

    result = DashboardService.delete_dashboard_item(item_id=item_id)
    return jsonify(result)


@dashboard_bp.route("/aggregate", methods=["GET"])
# @login_required
def get_aggregate_metrics():
    """Fetch aggregate metrics for the dashboard."""
    if current_user.role not in [UserRole.ADMIN.value, UserRole.USER.value]:
        return jsonify({"success": False, "error": "Access denied"})

    result = DashboardService.get_aggregate_metrics(user_id=current_user.id)
    if result["success"]:
        return jsonify({"success": True, "metrics": result["metrics"]})
    return jsonify({"success": False, "error": result["error"]})
