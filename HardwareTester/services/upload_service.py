
# upload_service.py

import os
from HardwareTester.utils.logger import Logger

logger = Logger(name="UploadService", log_file="logs/upload_service.log", level="INFO")

def upload_test_plan(file, uploaded_by):
    """Upload and save a test plan file."""
    try:
        # Save locally
        upload_dir = os.path.join("uploads", "test_plans")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        file.save(file_path)
        logger.info(f"Test plan uploaded by {uploaded_by}: {file_path}")
        return {"success": True, "message": f"Test plan '{file.filename}' uploaded successfully."}
    except Exception as e:
        logger.error(f"Failed to upload test plan: {e}")
        return {"success": False, "error": str(e)}

def upload_spec_sheet(file, uploaded_by):
    """Upload and save a spec sheet file."""
    try:
        # Save locally
        upload_dir = os.path.join("uploads", "spec_sheets")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        file.save(file_path)
        logger.info(f"Spec sheet uploaded by {uploaded_by}: {file_path}")
        return {"success": True, "message": f"Spec sheet '{file.filename}' uploaded successfully."}
    except Exception as e:
        logger.error(f"Failed to upload spec sheet: {e}")
        return {"success": False, "error": str(e)}

