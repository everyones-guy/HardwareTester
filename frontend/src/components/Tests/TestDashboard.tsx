import React, { useState } from "react";
import CodeScanner from "./CodeScanner";
import TestPlanManager from "./TestPlanManager";
import TestResultsPanel from "./TestResultsPanel";
import TestEditor from "./TestEditor";
import TestConfigForm from "./TestConfigForm";
import TestRunnerPanel from "./TestRunnerPanel";
import TestSuiteSelector from "./TestSuiteSelector";
import TestScheduleManager from "./TestScheduleManager";
import "./TestsDashboard.css";

const tabs = [
    "Plans",
    "Results",
    "Editor",
    "Scanner",
    "Config",
    "Runner",
    "Suites",
    "Schedule",
];

const TestsDashboard: React.FC = () => {
    const [activeTab, setActiveTab] = useState<string>("Plans");

    const renderTab = () => {
        switch (activeTab) {
            case "Plans":
                return <TestPlanManager />;
            case "Results":
                return <TestResultsPanel />;
            case "Editor":
                return <TestEditor />;
            case "Scanner":
                return <CodeScanner />;
            case "Config":
                return <TestConfigForm />;
            case "Runner":
                return <TestRunnerPanel />;
            case "Suites":
                return <TestSuiteSelector />;
            case "Schedule":
                return <TestScheduleManager />;
            default:
                return null;
        }
    };

    return (
        <div className="tests-dashboard">
            <h1>Tests Dashboard</h1>
            <div className="tab-bar">
                {tabs.map((tab) => (
                    <button
                        key={tab}
                        className={activeTab === tab ? "active" : ""}
                        onClick={() => setActiveTab(tab)}
                    >
                        {tab}
                    </button>
                ))}
            </div>

            <div className="tab-content">
                {renderTab()}
            </div>
        </div>
    );
};

export default TestsDashboard;
