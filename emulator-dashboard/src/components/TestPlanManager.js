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

    // Fetch available test plans (with retry logic)
    const fetchTestPlans = async (attempts = 3) => {
        try {
            const response = await axios.get("/api/test-plans");
            setTestPlans(response.data);
        } catch (error) {
            console.error("Error fetching test plans:", error);
            if (attempts > 1) {
                setTimeout(() => fetchTestPlans(attempts - 1), 2000);
            }
        }
    };

    // Fetch connected hardware info (with retry logic)
    const fetchHardwareInfo = async (attempts = 3) => {
        try {
            const response = await axios.get("/api/hardware/info");
            setHardwareInfo(response.data);
        } catch (error) {
            console.error("Error fetching hardware info:", error);
            if (attempts > 1) {
                setTimeout(() => fetchHardwareInfo(attempts - 1), 2000);
            }
        }
    };

    // Execute a test plan
    const runTestPlan = async () => {
        if (!selectedTestPlan) return alert("Select a test plan first!");

        setIsRunning(true);
        setExecutionLog((prevLogs) => [...prevLogs, `Starting test plan: ${selectedTestPlan.name}`]);

        try {
            const response = await axios.post("/api/test-plans/execute", { testPlanId: selectedTestPlan.id });

            setExecutionLog((prevLogs) => [...prevLogs, ...response.data.logs]);
            alert(`Test plan "${selectedTestPlan.name}" completed.`);
        } catch (error) {
            console.error("Error executing test plan:", error);
            setExecutionLog((prevLogs) => [...prevLogs, "Error executing test plan."]);
        }

        setIsRunning(false);
    };

    // Abort test plan execution
    const abortTestPlan = async () => {
        try {
            await axios.post("/api/test-plans/abort");
            setExecutionLog((prevLogs) => [...prevLogs, "Test plan aborted."]);
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
                        const plan = testPlans.find((p) => String(p.id) === e.target.value);
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
