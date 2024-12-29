
from flask import Blueprint, jsonify, request, render_template
from HardwareTester.services.test_plan_service import list_test_plans, upload_test_plan, run_test_plan

test_plan_bp = Blueprint("test_plan", __name__)

@test_plan_bp.route("/upload", methods=["POST"])
def upload_plan():
    """Upload a test plan."""
    file = request.files.get("file")
    uploaded_by = request.form.get("uploaded_by", "Unknown")
    result = upload_test_plan(file, uploaded_by)
    if result["success"]:
        return jsonify({"success": True, "message": result["message"]})
    return jsonify({"success": False, "error": result["error"]}), 400

@test_plan_bp.route("/<int:test_plan_id>/run", methods=["POST"])
def execute_plan(test_plan_id):
    """Run a specific test plan."""
    result = run_test_plan(test_plan_id)
    if result["success"]:
        return jsonify({"success": True, "results": result["results"]})
    return jsonify({"success": False, "error": result["error"]}), 400

@test_plan_bp.route("/test-plans", methods=["GET"])
def show_test_plans():
    """Render the test plan management page."""
    return render_template("test_plan_management.html")


@test_plan_bp.route("/test-plans/list", methods=["GET"])
def get_test_plans():
    """Get a list of all test plans."""
    response = list_test_plans()
    return jsonify(response)


@test_plan_bp.route("/test-plans/upload", methods=["POST"])
def upload_test_plan_endpoint():
    """Upload a new test plan."""
    file = request.files.get("file")
    uploaded_by = request.form.get("uploaded_by", "Unknown User")
    response = upload_test_plan(file, uploaded_by)
    return jsonify(response)


@test_plan_bp.route("/test-plans/run/<int:test_plan_id>", methods=["POST"])
def run_test_plan_endpoint(test_plan_id):
    """Run a specific test plan."""
    response = run_test_plan(test_plan_id)
    return jsonify(response)
	

