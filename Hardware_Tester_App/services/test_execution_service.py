from flask import Flask, request, jsonify
import threading
import time
import random

app = Flask(__name__)

# Simulated test execution states
test_plans = {}
test_results = {}

def execute_test_plan(test_id):
    """Simulates executing a test plan step-by-step."""
    test_plans[test_id]["status"] = "running"
    test_plans[test_id]["logs"].append(f"Test {test_id} started.")

    for step in test_plans[test_id]["steps"]:
        time.sleep(random.uniform(1, 3))  # Simulate execution time
        test_plans[test_id]["logs"].append(f"Step {step} completed.")
    
    # Simulated pass/fail result
    result = "pass" if random.random() > 0.1 else "fail"
    test_results[test_id] = result
    test_plans[test_id]["status"] = "completed"
    test_plans[test_id]["logs"].append(f"Test {test_id} completed with result: {result}")

@app.route("/api/test-plans/execute", methods=["POST"])
def start_test_plan():
    """Starts a test plan execution in a background thread."""
    data = request.json
    test_id = data.get("testPlanId")

    if not test_id or test_id not in test_plans:
        return jsonify({"error": "Invalid test plan ID"}), 400

    if test_plans[test_id]["status"] == "running":
        return jsonify({"error": "Test is already running"}), 400

    # Start test execution in a separate thread
    thread = threading.Thread(target=execute_test_plan, args=(test_id,))
    thread.start()

    return jsonify({"message": f"Test plan {test_id} started."})

@app.route("/api/test-plans/status/<test_id>", methods=["GET"])
def get_test_status(test_id):
    """Fetches the current status of a test plan."""
    if test_id not in test_plans:
        return jsonify({"error": "Test plan not found"}), 404

    return jsonify({
        "testId": test_id,
        "status": test_plans[test_id]["status"],
        "logs": test_plans[test_id]["logs"],
        "result": test_results.get(test_id, "pending"),
    })

@app.route("/api/test-plans/create", methods=["POST"])
def create_test_plan():
    """Creates a new test plan."""
    data = request.json
    test_id = data.get("id")

    if not test_id:
        return jsonify({"error": "Missing test ID"}), 400

    test_plans[test_id] = {
        "id": test_id,
        "name": data.get("name", f"Test Plan {test_id}"),
        "steps": data.get("steps", []),
        "status": "pending",
        "logs": []
    }

    return jsonify({"message": f"Test plan {test_id} created."})

@app.route("/api/test-plans", methods=["GET"])
def list_test_plans():
    """Returns a list of available test plans."""
    return jsonify(list(test_plans.values()))

if __name__ == "__main__":
    app.run(debug=True, port=5001)

