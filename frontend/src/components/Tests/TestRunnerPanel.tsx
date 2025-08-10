import React from "react";
import "./TestRunnerPanel.css";

const TestRunnerPanel: React.FC = () => {
    const handleRunAll = async () => {
        try {
            const res = await fetch("/tests/run-all", { method: "POST" });
            if (res.ok) alert("Tests started.");
            else throw new Error("Run failed.");
        } catch (err) {
            console.error("Failed to run tests:", err);
        }
    };

    return (
        <div className="test-runner-panel">
            <h3>Run Tests</h3>
            <button onClick={handleRunAll}>Run All</button>
        </div>
    );
};

export default TestRunnerPanel;
