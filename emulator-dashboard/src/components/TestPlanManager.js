import React, { useState, useEffect } from "react";
import axios from "axios";

const TestPlanManager = () => {
    const [testPlans, setTestPlans] = useState([]);
    const [selectedTestPlan, setSelectedTestPlan] = useState(null);
    const [executionLog, setExecutionLog] = useState([]);
    const [isRunning, setIsRunning] = useState(false);
    const [hardwareInfo, setHardwareInfo] = useState(null);

    useEffect(() => {
        fetchTestPlans();
        fetchHardwareInfo();
    }, []);

    // Fetch available test plans
    const fetchTestPlans = async () => {
        try {
            const response = await axios.get("/api/test-plans");
            setTestPlans(response.data);
        } catch (error) {
            console.error("Error fetching test plans:", error);
        }
    };

    // Fetch connected hardware info
    const fetchHardwareInfo = async () => {
        try {
            const response = await axios.get("/api/hardware/info");
            setHardwareInfo(response.data);
        } catch (error) {
            console.error("Error fetching hardware info:", error);
        }
    };

    // Execute a test plan
    const runTestPlan = async () => {
        if (!selectedTestPlan) return alert("Select a test plan first!");

        setIsRunning(true);
        setExecutionLog([...executionLog, `Starting test plan: ${selectedTestPlan.name}`]);

        try {
            const response = await axios.post("/api/test-plans/execute", { testPlanId: selectedTestPlan.id });

            setExecutionLog([...executionLog, ...response.data.logs]);
            alert(`Test plan "${selectedTestPlan.name}" completed.`);
        } catch (error) {
            console.error("Error executing test plan:", error);
            setExecutionLog([...executionLog, "Error executing test plan."]);
        }

        setIsRunning(false);
    };

    // Abort test plan execution
    const abortTestPlan = async () => {
        try {
            await axios.post("/api/test-plans/abort");
            setExecutionLog([...executionLog, "Test plan aborted."]);
            setIsRunning(false);
        } catch (error) {
            console.error("Error aborting test plan:", error);
        }
    };

    return (
        <div className="test-plan-manager">
            <h1>Test Plan Manager</h1>

            {/* Hardware Info Display */}
            <div>
                <h3>Detected Hardware</h3>
                {hardwareInfo ? (
                    <pre>{JSON.stringify(hardwareInfo, null, 2)}</pre>
                ) : (
                    <p>No hardware detected.</p>
                )}
            </div>

            {/* Test Plan Selection */}
            <div>
                <label>Select Test Plan:</label>
                <select
                    value={selectedTestPlan ? selectedTestPlan.id : ""}
                    onChange={(e) => {
                        const plan = testPlans.find((p) => p.id === e.target.value);
                        setSelectedTestPlan(plan);
                    }}
                >
                    <option value="">-- Choose a test plan --</option>
                    {testPlans.map((plan) => (
                        <option key={plan.id} value={plan.id}>
                            {plan.name}
                        </option>
                    ))}
                </select>
            </div>

            {/* Start/Abort Buttons */}
            <div>
                {!isRunning ? (
                    <button onClick={runTestPlan} disabled={!selectedTestPlan}>
                        Start Test Plan
                    </button>
                ) : (
                    <button onClick={abortTestPlan}>Abort Test Plan</button>
                )}
            </div>

            {/* Execution Log */}
            <div>
                <h3>Execution Log</h3>
                <textarea value={executionLog.join("\n")} readOnly rows="10" cols="50" />
            </div>
        </div>
    );
};

export default TestPlanManager;
