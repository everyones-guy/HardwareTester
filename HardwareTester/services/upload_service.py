import os
from werkzeug.datastructures import FileStorage
from HardwareTester.utils.custom_logger import CustomLogger

# Initialize logger
logger = CustomLogger.get_logger("upload_service")

class UploadService:
    """Service for handling file uploads."""

    @staticmethod
    def upload_file(file: FileStorage, file_type: str, uploaded_by: str) -> dict:
        """
        Upload and save a file to the appropriate directory.
        :param file: File object to be uploaded.
        :param file_type: Type of file (e.g., 'test_plans', 'spec_sheets').
        :param uploaded_by: User who uploaded the file.
        :return: Success or error message.
        """
        if not file:
            logger.error("No file provided for upload.")
            return {"success": False, "error": "No file provided."}

        try:
            # Determine upload directory
            upload_dir = os.path.join("uploads", file_type)
            os.makedirs(upload_dir, exist_ok=True)

            # Save the file
            file_path = os.path.join(upload_dir, file.filename)
            file.save(file_path)
            logger.info(f"File uploaded by {uploaded_by} to '{file_type}': {file_path}")
            return {"success": True, "message": f"File '{file.filename}' uploaded successfully to '{file_type}'."}
        except Exception as e:
            logger.error(f"Failed to upload file '{file.filename}' to '{file_type}': {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def upload_test_plan(file: FileStorage, uploaded_by: str) -> dict:
        """
        Upload and save a test plan file.
        :param file: File object to be uploaded.
        :param uploaded_by: User who uploaded the file.
        :return: Success or error message.
        """
        logger.info(f"Uploading test plan by {uploaded_by}...")
        return UploadService.upload_file(file, "test_plans", uploaded_by)

    @staticmethod
    def upload_spec_sheet(file: FileStorage, uploaded_by: str) -> dict:
        """
        Upload and save a spec sheet file.
        :param file: File object to be uploaded.
        :param uploaded_by: User who uploaded the file.
        :return: Success or error message.
        """
        logger.info(f"Uploading spec sheet by {uploaded_by}...")
        return UploadService.upload_file(file, "spec_sheets", uploaded_by)

    @staticmethod
    def validate_json(file):
        """Validate the uploaded JSON file."""
        try:
            json_data = json.load(file)
            return {"success": True, "data": json_data}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON file: {e}")
            return {"success": False, "error": str(e)}
    
    
# Usage:
# from werkzeug.datastructures import FileStorage
#
# # Example FileStorage object for testing
# file = FileStorage(
#     stream=open("example_test_plan.txt", "rb"),
#     filename="example_test_plan.txt",
#     content_type="text/plain",
# )
#
# result = UploadService.upload_test_plan(file, uploaded_by="test_user")
# print(result)
#
# Spec sheet example 
# 
# from werkzeug.datastructures import FileStorage
#
##  Example FileStorage object for testing
# file = FileStorage(
#     stream=open("example_spec_sheet.pdf", "rb"),
#     filename="example_spec_sheet.pdf",
#     content_type="application/pdf",
# )
#
# result = UploadService.upload_spec_sheet(file, uploaded_by="test_user")
# print(result)
