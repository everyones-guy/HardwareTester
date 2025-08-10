import React, { useState } from "react";
import "./TestEditor.css";

const TestEditor: React.FC = () => {
    const [code, setCode] = useState<string>("");

    const handleSave = async () => {
        try {
            const res = await fetch("/tests/save", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code }),
            });

            if (res.ok) alert("Test saved.");
            else throw new Error("Failed to save.");
        } catch (err) {
            console.error("Error saving test:", err);
        }
    };

    return (
        <div className="test-editor">
            <h3>Test Editor</h3>
            <textarea
                rows={10}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="Write or paste test code here..."
            />
            <button onClick={handleSave}>Save</button>
        </div>
    );
};

export default TestEditor;
