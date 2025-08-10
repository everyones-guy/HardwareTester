// /src/Tests/TestPlanManager.tsx

import React, { useState, useEffect } from "react";
import axios from "@/services/axiosInstance";
import "./TestPlanManager.css";

interface TestPlan {
    id: string;
    name: string;
}

interface HardwareInfo {
    [key: string]: any;
}

const TestPlanManager: React.FC = () => {
    const [testPlans, setTestPlans] = useState<TestPlan[]>([]);
    const [selectedTestPlan, setSelectedTestPlan] = useState<TestPlan | null>(null);
    const [executionLog, setExecutionLog] = useState<string[]>([]);
    const [isRunning, setIsRunning] = useState(false);
    const [hardwareInfo, setHardwareInfo] = useState<HardwareInfo | null>(null);

    useEffect(() => {
        fetchTestPlans();
        fetchHardwareInfo();
    }, []);

    const fetchTestPlans = async (attempts = 3) => {
        try {
            const res = await axios.get("/test-plans");
            setTestPlans(res.data);
        } catch (err) {
            console.error("Failed to fetch test plans:", err);
            if (attempts > 1) {
                setTimeout(() => fetchTestPlans(attempts - 1), 2000);
            }
        }
    };

    const fetchHardwareInfo = async (attempts = 3) => {
        try {
            const res = await axios.get("/hardware/info");
            setHardwareInfo(res.data);
        } catch (err) {
            console.error("Failed to fetch hardware info:", err);
            if (attempts > 1) {
                setTimeout(() => fetchHardwareInfo(attempts - 1), 2000);
            }
        }
    };

    const runTestPlan = async () => {
        if (!selectedTestPlan) return alert("Select a test plan first!");

        setIsRunning(true);
        log(`Starting test plan: ${selectedTestPlan.name}`);

        try {
            const res = await axios.post("/test-plans/execute", {
                testPlanId: selectedTestPlan.id,
            });

            if (res.data?.logs) {
                log(...res.data.logs);
            }

            alert(`Test plan "${selectedTestPlan.name}" completed.`);
        } catch (err) {
            console.error("Error executing test plan:", err);
            log("Error executing test plan.");
        }

        setIsRunning(false);
    };

    const abortTestPlan = async () => {
        try {
            await axios.post("/test-plans/abort");
            log("Test plan aborted.");
            setIsRunning(false);
        } catch (err) {
            console.error("Error aborting test plan:", err);
        }
    };

    const log = (...messages: string[]) => {
        setExecutionLog((prev) => [...prev, ...messages]);
    };

    return (
        <div className="test-plan-manager">
            <h2>Test Plan Manager</h2>

            {/* Hardware Info */}
            <section>
                <h4>Detected Hardware</h4>
                {hardwareInfo ? (
                    <pre>{JSON.stringify(hardwareInfo, null, 2)}</pre>
                ) : (
                    <p>No hardware detected.</p>
                )}
            </section>

            {/* Test Plan Selection */}
            <section>
                <label>Select Test Plan:</label>
                <select
                    value={selectedTestPlan?.id ?? ""}
                    onChange={(e) => {
                        const plan = testPlans.find((p) => p.id === e.target.value);
                        setSelectedTestPlan(plan ?? null);
                    }}
                >
                    <option value="">-- Choose a test plan --</option>
                    {testPlans.map((plan) => (
                        <option key={plan.id} value={plan.id}>
                            {plan.name}
                        </option>
                    ))}
                </select>
            </section>

            {/* Controls */}
            <div className="test-controls">
                {!isRunning ? (
                    <button onClick={runTestPlan} disabled={!selectedTestPlan}>
                        Start Test Plan
                    </button>
                ) : (
                    <button onClick={abortTestPlan}>Abort Test Plan</button>
                )}
            </div>

            {/* Logs */}
            <section>
                <h4>Execution Log</h4>
                <textarea
                    value={executionLog.join("\n")}
                    readOnly
                    rows={12}
                />
            </section>
        </div>
    );
};

export default TestPlanManager;
