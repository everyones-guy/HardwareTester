import React, { useState } from "react";
import { analyzeSourceCode } from "@/services/codeAnalyzerService";
import "./CodeScanner.css";

const CodeScanner: React.FC = () => {
    const [filePath, setFilePath] = useState<string>("");
    const [language, setLanguage] = useState<string>("c_sharp");
    const [analysisResult, setAnalysisResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    const handleAnalyze = async () => {
        try {
            const result = await analyzeSourceCode(filePath, language);
            setAnalysisResult(result);
            setError(null);
        } catch (err) {
            console.error("Failed to analyze source code", err);
            setError("Code analysis failed.");
        }
    };

    return (
        <div className="code-scanner">
            <h2>Code Scanner</h2>
            <div className="input-row">
                <input
                    type="text"
                    placeholder="Enter file path"
                    value={filePath}
                    onChange={(e) => setFilePath(e.target.value)}
                />
                <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                    <option value="c_sharp">C#</option>
                    <option value="cpp">C++</option>
                    <option value="javascript">JavaScript</option>
                    {/* Add more languages supported by Tree-sitter */}
                </select>
                <button onClick={handleAnalyze}>Analyze</button>
            </div>

            {error && <p className="error">{error}</p>}

            {analysisResult && (
                <div className="analysis-output">
                    <h4>Analysis Result</h4>
                    <pre>{JSON.stringify(analysisResult, null, 2)}</pre>
                </div>
            )}
        </div>
    );
};

export default CodeScanner;
