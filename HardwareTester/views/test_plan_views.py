from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from HardwareTester.services.test_plan_service import TestPlanService
from HardwareTester.extensions import logger

# Define the Blueprint for test plan management
test_plan_bp = Blueprint("test_plans", __name__, url_prefix="/test-plans")


@test_plan_bp.route("/", methods=["GET"])
@login_required
def show_test_plans():
    """
    Render the test plan management page.
    """
    return render_template("test_plan_management.html")


@test_plan_bp.route("/upload", methods=["POST"])
@login_required
def upload_plan():
    """
    Upload a test plan file.
    """
    file = request.files.get("file")
    uploaded_by = current_user.username if current_user.is_authenticated else "Unknown"

    result = TestPlanService.upload_test_plan(file, uploaded_by)
    return jsonify(result) if result["success"] else jsonify(result), 400


@test_plan_bp.route("/<int:test_plan_id>/run", methods=["POST"])
@login_required
def execute_plan(test_plan_id):
    """
    Run a specific test plan.
    """
    result = TestPlanService.run_test_plan(test_plan_id)
    return jsonify(result) if result["success"] else jsonify(result), 400


@test_plan_bp.route("/list", methods=["GET"])
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



@test_plan_bp.route("/<int:test_plan_id>/preview", methods=["GET"])
@login_required
def preview_test_plan(test_plan_id):
    """
    Preview a specific test plan.
    """
    result = TestPlanService.preview_test_plan(test_plan_id)
    return jsonify(result) if result["success"] else jsonify(result), 400


@test_plan_bp.route("/create", methods=["POST"])
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


@test_plan_bp.route("/<int:plan_id>/steps", methods=["POST"])
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
