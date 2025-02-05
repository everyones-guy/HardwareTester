from HardwareTester.extensions import db, logger
from HardwareTester.models.test_models import TestPlan, TestStep
import os
import psutil


class TestPlanService:
    @staticmethod
    def list_test_plans(search=None, page=1, per_page=10):
        """
        List all test plans with optional search and pagination.
        """
        try:
            query = TestPlan.query
            if search:
                query = query.filter(TestPlan.name.ilike(f"%{search}%"))

            paginated = query.paginate(page=page, per_page=per_page, error_out=False)

            test_plans = [
                {"id": plan.id, "name": plan.name, "description": plan.description}
                for plan in paginated.items
            ]
            return {"success": True, "testPlans": test_plans, "total": paginated.total}
        except Exception as e:
            logger.error(f"Error listing test plans: {e}")
            return {"success": False, "error": "An error occurred while listing test plans."}

    @staticmethod
    def upload_test_plan(file, uploaded_by):
        """
        Upload a test plan file and log it in the database.
        """
        try:
            if not file:
                return {"success": False, "error": "No file provided."}

            # Save the file to the uploads directory
            upload_dir = "uploads/test_plans"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, file.filename)
            file.save(file_path)

            # Create a test plan entry in the database
            test_plan = TestPlan(name=file.filename, description="Uploaded file", created_by=uploaded_by)
            db.session.add(test_plan)
            db.session.commit()

            logger.info(f"Test plan uploaded and saved: {file_path}")
            return {"success": True, "message": "Test plan uploaded successfully.", "test_plan": test_plan.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error uploading test plan: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def run_test_plan(test_plan_id):
        """
        Execute a test plan by ID.
        """
        try:
            test_plan = TestPlan.query.get(test_plan_id)
            if not test_plan:
                return {"success": False, "error": "Test plan not found."}

            # Placeholder for actual test execution logic
            logger.info(f"Running test plan: {test_plan.name}")
            return {"success": True, "results": [{"step": "Step 1", "result": "Passed"}]}
        except Exception as e:
            logger.error(f"Error running test plan ID {test_plan_id}: {e}")
            return {"success": False, "error": "An error occurred while running the test plan."}


    @staticmethod
    def preview_test_plan(test_plan_id):
        """
        Preview the details of a test plan.
        """
        try:
            test_plan = TestPlan.query.get(test_plan_id)
            if not test_plan:
                return {"success": False, "error": "Test plan not found."}

            steps = [{"action": step.action, "parameter": step.parameter} for step in test_plan.steps]
            return {"success": True, "plan": {"name": test_plan.name, "description": test_plan.description, "steps": steps}}
        except Exception as e:
            logger.error(f"Error previewing test plan ID {test_plan_id}: {e}")
            return {"success": False, "error": "An error occurred while previewing the test plan."}

    @staticmethod
    def create_test_plan(data, created_by):
        """
        Create a new test plan and ensure it's committed to the database.
        """
        try:
            test_plan = TestPlan(name=data["name"], description=data.get("description", ""), created_by=created_by)
            db.session.add(test_plan)
            db.session.commit()
            logger.info(f"Test plan '{test_plan.name}' created successfully.")
            return {"success": True, "test_plan": test_plan.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating test plan: {e}")
            return {"success": False, "error": str(e)}


    @staticmethod
    def add_test_step(plan_id, data, created_by):
        """
        Add a test step to a specific test plan and ensure it's committed.
        """
        try:
            test_plan = TestPlan.query.get(plan_id)
            if not test_plan:
                return {"success": False, "error": "Test plan not found."}

            test_step = TestStep(action=data["action"], parameter=data.get("parameter", ""), created_by=created_by, test_plan_id=plan_id)
            db.session.add(test_step)
            db.session.commit()
            logger.info(f"Test step added to test plan ID {plan_id}.")
            return {"success": True, "test_step": test_step.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding test step to test plan ID {plan_id}: {e}")
            return {"success": False, "error": str(e)}

    

        @staticmethod
        def get_test_metrics():
            """
            Fetch test execution metrics such as total test plans, passed tests, failed tests, and average execution time.
            :return: JSON response with test metrics
            """
            try:
                total_test_plans = db.session.query(TestPlan).count()
                total_test_steps = db.session.query(TestStep).count()
                passed_tests = db.session.query(TestStep).filter_by(result="Passed").count()
                failed_tests = db.session.query(TestStep).filter_by(result="Failed").count()

                test_metrics = {
                    "total_test_plans": total_test_plans,
                    "total_test_steps": total_test_steps,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "pass_rate": f"{(passed_tests / total_test_steps) * 100:.2f}%" if total_test_steps > 0 else "0%",
                    "status": "OK"
                }
                logger.info("Fetched test metrics successfully")
                return {"success": True, "data": test_metrics}
            except Exception as e:
                logger.error(f"Error fetching test metrics: {e}")
                return {"success": False, "error": str(e)}
