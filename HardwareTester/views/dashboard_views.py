from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from HardwareTester.services.dashboard_service import DashboardService
from HardwareTester.services.test_plan_service import TestPlanService
from HardwareTester.services.system_status_service import SystemStatusService
from HardwareTester.models.user_models import UserRole
from HardwareTester.extensions import logger
#from HardwareTester.utils.custom_logger import CustomLogger

# Initialize logger
#logger = CustomLogger.get_logger("dashboard_views")

logger.info("DASHBOARD_VIEWS")

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@dashboard_bp.route("/", methods=["GET"])
@login_required
def dashboard():
    """Render the dashboard homepage."""
    if current_user.role not in [UserRole.ADMIN.value, UserRole.USER.value]:
        return render_template("error.html", message="Access denied")

    # Fetch data for the dashboard
    dashboard_data = DashboardService.get_dashboard_data(user_id=current_user.id)
    if not dashboard_data["success"]:
        logger.error(f"Failed to fetch dashboard data: {dashboard_data['error']}")
        return render_template("error.html", message="Failed to load dashboard data.")

    return render_template("dashboard.html", data=dashboard_data["data"])

@dashboard_bp.route("/data", methods=["GET"])
@login_required
def get_dashboard_data():
    """Fetch dashboard data for the current user."""
    if current_user.role not in [UserRole.ADMIN.value, UserRole.USER.value]:
        return jsonify({"success": False, "error": "Access denied"})

    result = DashboardService.get_dashboard_data(user_id=current_user.id)
    if result["success"]:
        return jsonify({"success": True, "data": result["data"]})
    return jsonify({"success": False, "error": result["error"]})

@dashboard_bp.route("/create", methods=["POST"])
@login_required
def create_dashboard_item():
    """Create a new dashboard item."""
    #if current_user.role != UserRole.ADMIN.value:
    if current_user.role not in [UserRole.ADMIN.value, UserRole.USER.value]:
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
@login_required
def update_dashboard_item(item_id):
    """Update an existing dashboard item."""
    if current_user.role not in [UserRole.ADMIN.value, UserRole.USER.value]:
        return jsonify({"success": False, "error": "Access denied"})

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
    if current_user.role not in [UserRole.ADMIN.value, UserRole.USER.value]:
        return jsonify({"success": False, "error": "Access denied"})

    result = DashboardService.delete_dashboard_item(item_id=item_id)
    return jsonify(result)

@dashboard_bp.route("/aggregate", methods=["GET"])
@login_required
def get_aggregate_metrics():
    """Fetch aggregate metrics for the dashboard."""
    if current_user.role not in [UserRole.ADMIN.value, UserRole.USER.value]:
        return jsonify({"success": False, "error": "Access denied"})

    result = DashboardService.get_aggregate_metrics(user_id=current_user.id)
    if result["success"]:
        return jsonify({"success": True, "metrics": result["metrics"]})
    return jsonify({"success": False, "error": result["error"]})

@dashboard_bp.route("/user-management", methods=["GET"])
@login_required
def user_management_page():
    """Render the User Management page."""
    if current_user.role not in [UserRole.ADMIN.value, UserRole.USER.value]:
        return render_template("error.html", message="Access denied")
    return render_template("user_management.html")

@dashboard_bp.route("/overview", methods=["GET"])
@login_required
def overview():
    """
    Route to handle the dashboard overview tab.
    """
    try:
        # Fetch the overview data for the logged-in user
        overview_data = DashboardService.get_dashboard_data(current_user.id)

        # Render the template or return JSON, depending on the request context
        if "application/json" in str(render_template("dashboard.html")):
            return jsonify(overview_data)
        return render_template("dashboard.html", data=overview_data)
    except Exception as e:
        logger.error(f"Error retrieving overview data: {e}")
        return jsonify({"success": False, "error": "Failed to load overview data."}), 500

@dashboard_bp.route("/dashboard/system-health", methods=["GET"])
@login_required
def dashboard_system_health():
    """
    View for fetching system health metrics from SystemStatusService.
    """
    if current_user.role not in [UserRole.ADMIN.value, UserRole.USER.value]:
        return jsonify({"success": False, "error": "Access denied"}), 403

    result = SystemStatusService.get_full_system_status()
    return jsonify(result)

@dashboard_bp.route("/dashboard/test-metrics", methods=["GET"])
@login_required
def dashboard_test_metrics():
    """
    View for fetching test execution metrics to display on the dashboard.
    """
    if current_user.role not in [UserRole.ADMIN.value, UserRole.USER.value]:
        return jsonify({"success": False, "error": "Access denied"}), 403

    result = TestPlanService.get_test_metrics()
    return jsonify(result)