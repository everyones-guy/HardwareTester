from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from Hardware_Tester_App.services.test_plan_service import TestPlanService
from Hardware_Tester_App.extensions import logger
from Hardware_Tester_App.models.user_models import UserRole

# Define the Blueprint for test plan management
test_plan_bp = Blueprint("test_plans", __name__)


@test_plan_bp.route("/test-plans", methods=["GET"])
@login_required
def show_test_plans():
    """
    Render the test plan management page.
    """
    return render_template("test_plan_management.html")


@test_plan_bp.route("/api/test-plans/upload", methods=["POST"])
@login_required
def upload_plan():
    """
    Upload a test plan file.
    """
    file = request.files.get("file")
    uploaded_by = current_user.username if current_user.is_authenticated else "Unknown"

    result = TestPlanService.upload_test_plan(file, uploaded_by)
    return jsonify(result) if result["success"] else jsonify(result), 400


@test_plan_bp.route("/api/test-plans/<int:test_plan_id>/run", methods=["POST"])
@login_required
def execute_plan(test_plan_id):
    """
    Run a specific test plan.
    """
    result = TestPlanService.run_test_plan(test_plan_id)
    return jsonify(result) if result["success"] else jsonify(result), 400


@test_plan_bp.route("/api/test-plans/list", methods=["GET"])
@login_required
def list_test_plans():
    """
    List all test plans with optional search and pagination.
    """
    try:
        search = request.args.get("search", "").strip()
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))

        result = TestPlanService.list_test_plans(search=search, page=page, per_page=per_page)
        if result["success"]:
            if not result["testPlans"]:  # Check if the testPlans list is empty
                return jsonify({
                    "success": True,
                    "message": "No test plans to display. Please upload a test plan to populate this list.",
                    "testPlans": []
                })
            return jsonify(result)
        return jsonify({"success": False, "error": result["error"]}), 500
    except Exception as e:
        logger.error(f"Error listing test plans: {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500



@test_plan_bp.route("/api/test-plans/<int:test_plan_id>/preview", methods=["GET"])
@login_required
def preview_test_plan(test_plan_id):
    """
    Preview a specific test plan.
    """
    result = TestPlanService.preview_test_plan(test_plan_id)
    return jsonify(result) if result["success"] else jsonify(result), 400


@test_plan_bp.route("/api/test-plans/create", methods=["POST"])
@login_required
def create_test_plan():
    """
    Create a new test plan.
    """
    try:
        data = request.json
        created_by = current_user.id

        result = TestPlanService.create_test_plan(data, created_by)
        return jsonify(result) if result["success"] else jsonify(result), 400
    except Exception as e:
        logger.error(f"Error creating test plan: {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500


@test_plan_bp.route("/api/test-plans/<int:plan_id>/steps", methods=["POST"])
@login_required
def add_test_step(plan_id):
    """
    Add a test step to an existing test plan.
    """
    try:
        data = request.json
        created_by = current_user.id

        result = TestPlanService.add_test_step(plan_id, data, created_by)
        return jsonify(result) if result["success"] else jsonify(result), 400
    except Exception as e:
        logger.error(f"Error adding test step to plan ID {plan_id}: {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500

@test_plan_bp.route("/api/test-plans/<int:plan_id>/load", methods=["GET"])
def load_test_plan(plan_id):
    # Example plan data
    test_plan = {"id": plan_id, "name": f"Test Plan {plan_id}"}
    return jsonify({"success": True, "plan": test_plan})

@test_plan_bp.route("/api/test-plans/<int:test_plan_id>", methods=["DELETE"])
@login_required
def delete_test_plan(test_plan_id):
    try:
        result = TestPlanService.delete_test_plan(test_plan_id)
        return jsonify(result) if result["success"] else jsonify(result), 400
    except Exception as e:
        logger.error(f"Error deleting test plan ID {test_plan_id}: {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500


@test_plan_bp.route("/api/test-plans/test-metrics", methods=["GET"])
@login_required
def test_metrics():
    """
    API route to fetch test execution metrics.
    """
    if current_user.role not in [UserRole.ADMIN.value, UserRole.USER.value]:
        return jsonify({"success": False, "error": "Access denied"}), 403

    result = TestPlanService.get_test_metrics()
    return jsonify(result)
