
import os
from HardwareTester.utils.logger import Logger
from HardwareTester.utils.api_manager import create_api_manager

logger = Logger(name="TestPlanService", log_file="logs/test_plan_service.log", level="INFO")
api_manager = create_api_manager("https://127.0.0.1/api")


def list_test_plans():
    """Fetch and return all test plans."""
    logger.info("Fetching list of test plans...")
    response = api_manager.get("test-plans")
    if "error" in response:
        logger.error(f"Failed to fetch test plans: {response['error']}")
        return {"success": False, "error": response["error"]}
    logger.info(f"Retrieved {len(response.get('testPlans', []))} test plans.")
    return {"success": True, "testPlans": response.get("testPlans", [])}


def upload_test_plan(file, uploaded_by):
    """Upload a test plan file."""
    logger.info(f"Uploading test plan by {uploaded_by}...")
    if not file:
        logger.error("No file provided for upload.")
        return {"success": False, "error": "No file provided."}

    try:
        file_path = os.path.join("uploads/test_plans", file.filename)
        file.save(file_path)
        logger.info(f"Saved test plan locally: {file_path}")
        payload = {"uploaded_by": uploaded_by}
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = api_manager.post("test-plans/upload", payload=payload, headers={"files": files})
            if "error" in response:
                logger.error(f"Failed to upload test plan to API: {response['error']}")
                return {"success": False, "error": response["error"]}
        logger.info(f"Test plan uploaded successfully: {response}")
        return {"success": True, "message": "Test plan uploaded successfully."}
    except Exception as e:
        logger.error(f"Error uploading test plan: {e}")
        return {"success": False, "error": str(e)}


def run_test_plan(test_plan_id):
    """Run a specific test plan by ID."""
    logger.info(f"Running test plan ID {test_plan_id}...")
    response = api_manager.post(f"test-plans/{test_plan_id}/run")
    if "error" in response:
        logger.error(f"Failed to run test plan {test_plan_id}: {response['error']}")
        return {"success": False, "error": response["error"]}
    logger.info(f"Test plan executed successfully: {response}")
    return {"success": True, "results": response.get("results", [])}

