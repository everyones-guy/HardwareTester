
from HardwareTester.models import TestPlan

def run_test_plan(test_plan_id):
    """
    Run a test plan by executing its steps.
    :param test_plan_id: ID of the test plan in the database.
    :return: Results of the test run.
    """
    test_plan = TestPlan.query.get(test_plan_id)
    if not test_plan:
        return {"success": False, "message": "Test plan not found"}

    steps = test_plan.steps
    results = []

    for step in steps:
        # Simulate or execute the test step
        # Example: {"Step": "1", "Action": "Set Valve", "Parameter": "50% Open"}
        result = simulate_step(step)  # Replace with actual execution logic
        results.append({"step": step, "result": result})

    return {"success": True, "results": results}

def simulate_step(step):
    """
    Simulate a test step (placeholder for real execution).
    :param step: A single test step.
    :return: Simulated result.
    """
    return f"Executed step: {step.get('Action')} with parameter {step.get('Parameter')}"


