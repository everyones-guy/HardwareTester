from flask import Blueprint, jsonify, request
from HardwareTester.services.test_plan_service import list_test_plans, upload_test_plan, run_test_plan

test_plan_bp = Blueprint("test_plan", __name__)

@test_plan_bp.route("/", methods=["GET"])
def get_test_plans():
    """Get all test plans."""
    result = list_test_plans()
    if result["success"]:
        return jsonify({"success": True, "testPlans": result["testPlans"]})
    return jsonify({"success": False, "error": result["error"]}), 500

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
