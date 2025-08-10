import React, { useState, useEffect } from "react";
import { getTestMetrics, subscribeToTestMetrics } from "@/services/dashboardService";
import "./TestResultsPanel.css";

interface TestResult {
    testName: string;
    status: string;
    duration: number;
}

const TestResultsPanel: React.FC = () => {
    const [testResults, setTestResults] = useState<TestResult[]>([]);

    useEffect(() => {
        fetchResults();

        const unsubscribe = subscribeToTestMetrics((data: TestResult[]) => {
            setTestResults(data);
        });

        return () => {
            if (typeof unsubscribe === "function") unsubscribe();
        };
    }, []);

    const fetchResults = async () => {
        try {
            const data = await getTestMetrics();
            setTestResults(data ?? []);
        } catch (err) {
            console.error("Failed to fetch test results:", err);
        }
    };

    return (
        <div className="test-results-panel">
            <h2>Test Results</h2>
            <button onClick={fetchResults}>Refresh</button>

            <table>
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Status</th>
                        <th>Duration</th>
                    </tr>
                </thead>
                <tbody>
                    {testResults.length > 0 ? (
                        testResults.map((result, idx) => (
                            <tr key={idx}>
                                <td>{result.testName}</td>
                                <td className={result.status.toLowerCase()}>{result.status}</td>
                                <td>{result.duration} ms</td>
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td colSpan={3} style={{ textAlign: "center" }}>No test results available</td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default TestResultsPanel;
