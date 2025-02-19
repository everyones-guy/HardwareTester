import os
from dotenv import load_dotenv

from HardwareTester.utils.api_manager import create_api_manager
from HardwareTester.utils.custom_logger import CustomLogger

# Load environment variables from .env
load_dotenv()

# Initialize Logger
logger = CustomLogger.get_logger("test_plan_manager")

# Initialize APIManager
api_manager = create_api_manager(os.getenv("BASE_API_URL", "http://localhost:5000/api"))

def list_test_plans():
    """Fetch and display all test plans."""
    logger.info("Fetching list of test plans...")
    response = api_manager.get("test-plans")
    if "error" in response:
        logger.error(f"Failed to fetch test plans: {response['error']}")
        return
    test_plans = response.get("testPlans", [])
    logger.info(f"Retrieved {len(test_plans)} test plans.")
    for plan in test_plans:
        print(f"ID: {plan['id']}, Name: {plan['name']}, Uploaded By: {plan['uploaded_by']}")

def upload_test_plan(file_path, uploaded_by):
    """Upload a new test plan."""
    logger.info(f"Uploading test plan from file: {file_path}")
    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path, f)}
            response = api_manager.post("test-plans/upload", payload={"uploaded_by": uploaded_by}, headers={"files": files})
            if "error" in response:
                logger.error(f"Failed to upload test plan: {response['error']}")
                return
            logger.info(f"Test plan uploaded successfully: {response}")
            print(f"Uploaded Test Plan: {response}")
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

def delete_test_plan(plan_id):
    """Delete a test plan."""
    logger.info(f"Deleting test plan ID {plan_id}...")
    response = api_manager.delete(f"test-plans/{plan_id}")
    if "error" in response:
        logger.error(f"Failed to delete test plan {plan_id}: {response['error']}")
        return
    logger.info(f"Test plan deleted successfully: {response}")
    print(f"Deleted Test Plan ID {plan_id}")

if __name__ == "__main__":
    list_test_plans()
    upload_test_plan("path/to/test_plan.pdf", "Test User")
    delete_test_plan(1)
