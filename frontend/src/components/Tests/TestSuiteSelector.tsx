import React, { useState, useEffect } from "react";
import "./TestSuiteSelector.css";

interface TestSuite {
    id: string;
    name: string;
}

const TestSuiteSelector: React.FC = () => {
    const [suites, setSuites] = useState<TestSuite[]>([]);
    const [selected, setSelected] = useState<string>("");

    useEffect(() => {
        fetch("/tests/suites")
            .then((res) => res.json())
            .then(setSuites);
    }, []);

    return (
        <div className="test-suite-selector">
            <label>Test Suite:</label>
            <select value={selected} onChange={(e) => setSelected(e.target.value)}>
                <option value="">-- Select --</option>
                {suites.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                ))}
            </select>
        </div>
    );
};

export default TestSuiteSelector;
