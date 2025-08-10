// src/components/FirmwareDashboard/FirmwareValidator.tsx
import React, { useState } from "react";
import APIService from "@/services/apiService";
import "./FirmwareValidator.css";

interface ValidationResult {
    isValid: boolean;
    errors?: string[];
    warnings?: string[];
    metadata?: Record<string, string>;
}

const FirmwareValidator: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [result, setResult] = useState<ValidationResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const onPick = (f: File | null) => {
        setFile(f);
        setResult(null);
        setError(null);
    };

    const handleValidate = async () => {
        if (!file) return alert("Please select a firmware file.");

        const formData = new FormData();
        formData.append("firmware", file);

        try {
            setLoading(true);
            setError(null);

            // Do NOT set Content-Type; the browser will set multipart/form-data boundary
            const res = await APIService.apiCallWithRetry<any>(
                "firmware/validate",
                "POST",
                formData,
                {} // no headers
            );

            // Accept either {data: {...}} or raw object
            const data: ValidationResult = res?.data ?? res;
            setResult(data);
        } catch (err: any) {
            console.error("Validation error:", err);
            setError(err?.message || "Validation failed. Please try again.");
            setResult(null);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="firmware-validator">
            <h2>Firmware Validator</h2>

            <input
                type="file"
                onChange={(e) => onPick(e.target.files?.[0] || null)}
                accept=".bin,.fw,.hex"
            />
            <button onClick={handleValidate} disabled={!file || loading}>
                {loading ? "Validating..." : "Validate Firmware"}
            </button>

            {file && (
                <p className="file-hint">
                    Selected: <strong>{file.name}</strong> ({Math.ceil(file.size / 1024)} KB)
                </p>
            )}

            {error && <p className="validator-error">{error}</p>}

            {result && (
                <div className={`validation-result ${result.isValid ? "valid" : "invalid"}`}>
                    <h3>{result.isValid ? "Firmware is VALID" : "Firmware is INVALID"}</h3>

                    {result.errors?.length ? (
                        <div>
                            <h4>Errors</h4>
                            <ul>{result.errors.map((err, idx) => <li key={idx}>{err}</li>)}</ul>
                        </div>
                    ) : null}

                    {result.warnings?.length ? (
                        <div>
                            <h4>Warnings</h4>
                            <ul>{result.warnings.map((w, idx) => <li key={idx}>{w}</li>)}</ul>
                        </div>
                    ) : null}

                    {result.metadata ? (
                        <div>
                            <h4>Metadata</h4>
                            <ul>
                                {Object.entries(result.metadata).map(([k, v]) => (
                                    <li key={k}>
                                        <strong>{k}:</strong> {v}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ) : null}
                </div>
            )}
        </div>
    );
};

export default FirmwareValidator;
