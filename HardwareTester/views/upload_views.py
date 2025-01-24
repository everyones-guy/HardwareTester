

from flask import Blueprint, request, jsonify, render_template
from HardwareTester.services.upload_service import UploadService
from HardwareTester.services.hardware_service import HardwareService
from HardwareTester.utils.custom_logger import CustomLogger
import json
import os

# Initialize logger
logger = CustomLogger.get_logger("upload_views")

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
    
@upload_bp.route("/firmware/upload", methods=["POST"])
def upload_firmware():
    """Upload firmware and assign to machines."""
    firmware_file = request.files.get("firmware")
    machines = request.form.getlist("machines")  # Expecting a list of machine IDs

    if not firmware_file or not machines:
        return jsonify({"success": False, "error": "Firmware and machine list are required"}), 400

    firmware_result = HardwareService.process_uploaded_firmware(firmware_file)
    if "error" in firmware_result:
        return jsonify({"success": False, "error": firmware_result["error"]}), 500

    # Store firmware for each machine
    for machine_id in machines:
        # Assuming `update_device_firmware` exists in HardwareService
        result = HardwareService.update_device_status(machine_id, "firmware_uploaded")
        if not result["success"]:
            logger.error(f"Failed to assign firmware to machine {machine_id}: {result['error']}")

    return jsonify({"success": True, "message": "Firmware uploaded successfully", "hash": firmware_result["hash"]})


@upload_bp.route("/json/preview", methods=["POST"])
def preview_json():
    """Upload and preview a JSON file."""
    file = request.files.get("file")
    if not file or not file.filename.endswith('.json'):
        return jsonify({"success": False, "error": "Invalid or missing JSON file."}), 400

    try:
        json_data = file.read().decode("utf-8")
        return jsonify({"success": True, "data": json_data}), 200
    except Exception as e:
        logger.error(f"Error processing JSON preview: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@upload_bp.route("/json/save", methods=["POST"])
def save_json():
    """Save the modified JSON data."""
    try:
        modified_data = request.json.get("data")
        filename = request.json.get("filename", "modified_file.json")

        # Save the JSON data
        upload_dir = os.path.join("uploads", "json_files")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified_data)

        logger.info(f"Modified JSON saved to {file_path}")
        return jsonify({"success": True, "message": f"JSON saved successfully to {file_path}"}), 200
    except Exception as e:
        logger.error(f"Error saving JSON file: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
