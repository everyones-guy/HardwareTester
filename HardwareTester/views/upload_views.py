

from flask import Blueprint, request, jsonify, render_template
from HardwareTester.services.upload_service import UploadService

upload_bp = Blueprint("upload", __name__)

@upload_bp.route("/test-plans/upload", methods=["POST"])
def upload_test_plan_view():
    """Upload a test plan."""
    file = request.files.get("file")
    uploaded_by = request.form.get("uploaded_by", "Unknown")
    if not file:
        return jsonify({"success": False, "error": "No file provided."}), 400

    result = UploadService.upload_test_plan(file, uploaded_by)
    if result["success"]:
        return jsonify({"success": True, "message": result["message"]})
    else:
        return jsonify({"success": False, "error": result["error"]}), 500

@upload_bp.route("/spec-sheets/upload", methods=["POST"])
def upload_spec_sheet_view():
    """Upload a spec sheet."""
    file = request.files.get("file")
    uploaded_by = request.form.get("uploaded_by", "Unknown")
    if not file:
        return jsonify({"success": False, "error": "No file provided."}), 400

    result = UploadService.upload_spec_sheet(file, uploaded_by)
    if result["success"]:
        return jsonify({"success": True, "message": result["message"]})
    else:
        return jsonify({"success": False, "error": result["error"]}), 500

