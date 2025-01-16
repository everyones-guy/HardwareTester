from flask import Blueprint, jsonify, request, render_template
from HardwareTester.services.test_plan_service import TestPlanService
from HardwareTester.models.test_models import TestPlan
from HardwareTester.extensions import db

# Define the Blueprint for test plan management
test_plan_bp = Blueprint("test_plans", __name__, url_prefix="/test-plans")

@test_plan_bp.route("/", methods=["GET"])
def show_test_plans():
    """
    Render the test plan management page.
    Provides the main interface for managing test plans.
    """
    return render_template("test_plan_management.html")

@test_plan_bp.route("/upload", methods=["POST"])
def upload_plan():
    """
    Upload a test plan.
    Receives a file and the name of the uploader, then processes the test plan.
    """
    file = request.files.get("file")
    uploaded_by = request.form.get("uploaded_by", "Unknown")
    result = TestPlanService.upload_test_plan(file, uploaded_by)
    if result["success"]:
        return jsonify({"success": True, "message": result["message"]})
    return jsonify({"success": False, "error": result["error"]}), 400


@test_plan_bp.route("/<int:test_plan_id>/run", methods=["POST"])
def execute_plan(test_plan_id):
    """
    Run a specific test plan.
    Executes the test plan identified by the provided test_plan_id.
    """
    result = TestPlanService.run_test_plan(test_plan_id)
    if result["success"]:
        return jsonify({"success": True, "results": result["results"]})
    return jsonify({"success": False, "error": result["error"]}), 400

@test_plan_bp.route("/list", methods=["GET"])
def list_test_plans():
    try:
        # Replace with your actual query logic
        plans = TestPlan.query.all()
        if not plans:  # If no test plans exist
            return jsonify({"success": True, "testPlans": []})  # Return an empty list

        # Serialize the test plans
        return jsonify({"success": True, "testPlans": [plan.serialize() for plan in plans]})
    except Exception as e:
        app.logger.error(f"Error retrieving test plans: {e}")
        return jsonify({"success": False, "error": "Failed to retrieve test plans."}), 500


@test_plan_bp.route("/run/<int:test_plan_id>", methods=["POST"])
def run_test_plan_endpoint(test_plan_id):
    """
    Run a specific test plan.
    Executes the test plan identified by test_plan_id and returns the results.
    """
    response = TestPlanService.run_test_plan(test_plan_id)
    return jsonify(response)


@test_plan_bp.route("/<int:test_plan_id>/preview", methods=["GET"])
def preview_test_plan(test_plan_id):
    """
    Preview a specific test plan.
    Provides a detailed view of the test plan's steps and metadata.
    """
    response = TestPlanService.preview_test_plan(test_plan_id)
    if response["success"]:
        return jsonify({"success": True, "plan": response["plan"]})
    return jsonify({"success": False, "error": response["error"]}), 400

@test_plan_bp.route("/seed-test-plans", methods=["POST"])
def seed_test_plans():
    try:
        # Replace with your ORM or database logic
        test_plan = TestPlan(name="Sample Test Plan", uploaded_by="Admin")
        db.session.add(test_plan)
        db.session.commit()
        return jsonify({"success": True, "message": "Test plans seeded successfully."})
    except Exception as e:
        app.logger.error(f"Error seeding test plans: {e}")
        return jsonify({"success": False, "error": "Failed to seed test plans."}), 500
