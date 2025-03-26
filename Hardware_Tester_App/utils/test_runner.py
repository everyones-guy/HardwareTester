from Hardware_Tester_App.models.test_models import TestPlan, TestStep

def run_test_plan(test_plan_id):
    """
    Run a test plan by executing its steps.
    :param test_plan_id: ID of the test plan in the database.
    :return: Results of the test run.
    """
    # Fetch the test plan by ID
    test_plan = TestPlan.query.get(test_plan_id)
    if not test_plan:
        return {"success": False, "message": "Test plan not found"}

    results = []

    for step in test_plan.steps:
        # Simulate or execute the test step
        result = simulate_step(step)
        results.append({"step_id": step.id, "action": step.action, "parameter": step.parameter, "result": result})

    return {"success": True, "results": results}


def simulate_step(step):
    """
    Simulate a test step (placeholder for real execution).
    :param step: A TestStep instance.
    :return: Simulated result.
    """
    return f"Executed step: {step.action} with parameter {step.parameter}"
