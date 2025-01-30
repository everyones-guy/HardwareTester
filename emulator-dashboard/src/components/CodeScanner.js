import React, { useState } from "react";
import { analyzeSourceCode } from "../services/codeAnalyzerService";

const CodeScanner = () => {
    const [filePath, setFilePath] = useState("");
    const [language, setLanguage] = useState("");
    const [analysisResult, setAnalysisResult] = useState(null);

    const handleAnalyze = async () => {
        try {
            const result = await analyzeSourceCode(filePath, language);
            setAnalysisResult(result);
        } catch (error) {
            console.error("Failed to analyze source code");
        }
    };

    return (
        <div>
            <h2>Code Scanner</h2>
            <input type="text" placeholder="Enter File Path" onChange={(e) => setFilePath(e.target.value)} />
            <select onChange={(e) => setLanguage(e.target.value)}>
                <option value="csharp">C#</option>
                <option value="cpp">C++</option>
                <option value="javascript">JavaScript</option>
            </select>
            <button onClick={handleAnalyze}>Analyze</button>
            {analysisResult && <pre>{JSON.stringify(analysisResult, null, 2)}</pre>}
        </div>
    );
};

export default CodeScanner;
