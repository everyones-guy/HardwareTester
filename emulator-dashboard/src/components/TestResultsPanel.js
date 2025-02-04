import React, { useState, useEffect } from "react";
import { getTestMetrics, subscribeToTestMetrics } from "../services/dashboardService";

const TestResultsPanel = () => {
    const [testResults, setTestResults] = useState([]);

    useEffect(() => {
        fetchResults();

        // Subscribe to real-time test results
        const unsubscribe = subscribeToTestMetrics((data) => setTestResults(data));

        return () => unsubscribe(); // Cleanup WebSocket on unmount
    }, []);

    const fetchResults = async () => {
        const data = await getTestMetrics();
        setTestResults(data);
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
                                <td>{result.status}</td>
                                <td>{result.duration} ms</td>
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td colSpan="3" style={{ textAlign: "center" }}>No test results available</td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default TestResultsPanel;
