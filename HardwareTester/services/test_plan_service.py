# test_plan_service.py
# Handles operations around test plans, including listing, uploading, and running test plans.

import os
from HardwareTester.utils.api_manager import create_api_manager
from HardwareTester.extensions import logger

# Initialize logger and API manager
api_manager = create_api_manager("https://127.0.0.1/api")


class TestPlanService:
    """Service for managing test plans."""

    @staticmethod
    def list_test_plans() -> dict:
        """
        Fetch and return all test plans.
        :return: Dictionary containing test plans or an error message.
        """
        logger.info("Fetching list of test plans...")
        try:
            response = api_manager.get("test-plans")
            if "error" in response:
                logger.error(f"Failed to fetch test plans: {response['error']}")
                return {"success": False, "error": response["error"]}
            test_plans = response.get("testPlans", [])
            logger.info(f"Retrieved {len(test_plans)} test plans.")
            return {"success": True, "testPlans": test_plans}
        except Exception as e:
            logger.error(f"Unexpected error fetching test plans: {e}")
            return {"success": False, "error": "An unexpected error occurred while fetching test plans."}

    @staticmethod
    def upload_test_plan(file, uploaded_by: str) -> dict:
        """
        Upload a test plan file.
        :param file: File object to upload.
        :param uploaded_by: User who uploaded the file.
        :return: Success or error message.
        """
        logger.info(f"Uploading test plan by {uploaded_by}...")
        if not file:
            logger.error("No file provided for upload.")
            return {"success": False, "error": "No file provided."}

        try:
            # Save the file locally
            upload_dir = "uploads/test_plans"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, file.filename)
            file.save(file_path)
            logger.info(f"Saved test plan locally: {file_path}")

            # Prepare and send the API request
            payload = {"uploaded_by": uploaded_by}
            with open(file_path, "rb") as f:
                files = {"file": f}
                response = api_manager.post("test-plans/upload", payload=payload, files=files)
                if "error" in response:
                    logger.error(f"Failed to upload test plan to API: {response['error']}")
                    return {"success": False, "error": response["error"]}
            logger.info(f"Test plan uploaded successfully: {response}")
            return {"success": True, "message": "Test plan uploaded successfully."}
        except Exception as e:
            logger.error(f"Error uploading test plan: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def run_test_plan(test_plan_id: int) -> dict:
        """
        Run a specific test plan by ID.
        :param test_plan_id: ID of the test plan to run.
        :return: Results of the test plan or an error message.
        """
        logger.info(f"Running test plan ID {test_plan_id}...")
        try:
            response = api_manager.post(f"test-plans/{test_plan_id}/run")
            if "error" in response:
                logger.error(f"Failed to run test plan {test_plan_id}: {response['error']}")
                return {"success": False, "error": response["error"]}
            logger.info(f"Test plan executed successfully: {response}")
            return {"success": True, "results": response.get("results", [])}
        except Exception as e:
            logger.error(f"Unexpected error running test plan {test_plan_id}: {e}")
            return {"success": False, "error": "An unexpected error occurred while running the test plan."}
