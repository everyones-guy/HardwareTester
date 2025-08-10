// src/components/FirmwareDashboard/FirmwareDashboard.tsx
import React, { useState } from "react";
import FirmwareUploader from "./FirmwareUploader";
import FirmwareValidator from "./FirmwareValidator";
import FirmwareTableContainer from "./FirmwareTableContainer";
import "./FirmwareDashboard.css";

const FirmwareDashboard: React.FC = () => {
    const [reloadTick, setReloadTick] = useState(0);
    const [search, setSearch] = useState("");

    const handleUploadSuccess = () => {
        // bump the token to force the table to reload
        setReloadTick((n) => n + 1);
    };

    const handleUploadError = (_msg: string) => {
        // you could show a toast here if you like
    };

    return (
        <div className="firmware-dashboard">
            <div className="firmware-header">
                <h2>Firmware Dashboard</h2>

                <div className="firmware-actions">
                    <input
                        type="text"
                        placeholder="Search firmware..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
            </div>

            <div className="firmware-tools">
                <div className="tool-card">
                    <h3>Upload</h3>
                    <FirmwareUploader
                        onUploadSuccess={handleUploadSuccess}
                        onUploadError={handleUploadError}
                        acceptExtensions={[".bin", ".hex", ".fw"]}
                        allowMultiple={false}
                    />
                </div>

                <div className="tool-card">
                    <h3>Validate</h3>
                    <FirmwareValidator />
                </div>
            </div>

            <div className="firmware-list">
                <FirmwareTableContainer reloadToken={reloadTick} query={search} />
            </div>
        </div>
    );
};

export default FirmwareDashboard;
