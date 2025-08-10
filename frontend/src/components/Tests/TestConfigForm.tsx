import React, { useState } from "react";
import "./TestConfigForm.css";

const TestConfigForm: React.FC = () => {
    const [timeout, setTimeout] = useState(5000);
    const [retries, setRetries] = useState(3);

    return (
        <div className="test-config-form">
            <h3>Test Configuration</h3>
            <label>Timeout (ms)</label>
            <input
                type="number"
                value={timeout}
                onChange={(e) => setTimeout(parseInt(e.target.value))}
            />
            <label>Retries</label>
            <input
                type="number"
                value={retries}
                onChange={(e) => setRetries(parseInt(e.target.value))}
            />
        </div>
    );
};

export default TestConfigForm;
