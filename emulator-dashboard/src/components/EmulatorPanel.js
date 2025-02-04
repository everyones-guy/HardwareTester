import React, { useState, useEffect } from "react";
import {
    startEmulation,
    stopEmulation,
    getActiveEmulations,
    uploadFirmware,
    setTimedEvent,
    enableUIMirror,
    getEmulationLogs,
    exportLogs,
} from "../services/emulatorService";

const EmulatorPanel = () => {
    const [emulations, setEmulations] = useState([]);
    const [firmwareFile, setFirmwareFile] = useState(null);
    const [selectedEmulation, setSelectedEmulation] = useState(null);
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadEmulations();
    }, []);

    const loadEmulations = async () => {
        try {
            setLoading(true);
            const data = await getActiveEmulations();
            setEmulations(data);
            setError(null);
        } catch (err) {
            console.error("Error loading emulations:", err);
            setError("Failed to load emulations.");
        } finally {
            setLoading(false);
        }
    };

    const handleStartEmulation = async () => {
        try {
            setLoading(true);
            const emulationData = { deviceType: "CustomDevice", firmwareVersion: "1.0.0" };
            await startEmulation(emulationData);
            loadEmulations();
        } catch (err) {
            console.error("Error starting emulation:", err);
            setError("Failed to start emulation.");
        } finally {
            setLoading(false);
        }
    };

    const handleStopEmulation = async (emulationId) => {
        try {
            await stopEmulation(emulationId);
            loadEmulations();
        } catch (err) {
            console.error("Error stopping emulation:", err);
            setError("Failed to stop emulation.");
        }
    };

    const handleFirmwareUpload = async () => {
        if (!firmwareFile) return alert("Please select a firmware file.");
        try {
            await uploadFirmware(firmwareFile);
            alert("Firmware uploaded successfully!");
            setFirmwareFile(null);
        } catch (err) {
            console.error("Error uploading firmware:", err);
            setError("Firmware upload failed.");
        }
    };

    const handleSetTimedEvent = async () => {
        if (!selectedEmulation) return alert("Select an emulation first.");
        try {
            const eventConfig = { eventType: "trigger-action", triggerTime: Date.now() + 60000 };
            await setTimedEvent(selectedEmulation.id, eventConfig);
            alert("Timed event set successfully!");
        } catch (err) {
            console.error("Error setting timed event:", err);
            setError("Failed to set timed event.");
        }
    };

    const handleEnableMirror = async () => {
        if (!selectedEmulation) return alert("Select an emulation first.");
        try {
            await enableUIMirror(selectedEmulation.id);
            alert("UI Mirror enabled!");
        } catch (err) {
            console.error("Error enabling UI mirror:", err);
            setError("Failed to enable UI mirror.");
        }
    };

    const handleViewLogs = async (emulationId) => {
        try {
            const data = await getEmulationLogs(emulationId);
            setLogs(data);
        } catch (err) {
            console.error("Error fetching logs:", err);
            setError("Failed to fetch logs.");
        }
    };

    const handleExportLogs = async (emulationId) => {
        try {
            const data = await exportLogs(emulationId);
            const url = window.URL.createObjectURL(new Blob([data]));
            const link = document.createElement("a");
            link.href = url;
            link.setAttribute("download", `emulation_logs_${emulationId}.txt`);
            document.body.appendChild(link);
            link.click();
        } catch (err) {
            console.error("Error exporting logs:", err);
            setError("Failed to export logs.");
        }
    };

    return (
        <div className="emulator-panel">
            <h1>Emulator Dashboard</h1>

            {error && <p className="error">{error}</p>}

            <button onClick={handleStartEmulation} disabled={loading}>
                {loading ? "Starting..." : "Start New Emulation"}
            </button>

            <h2>Active Emulations</h2>
            {loading ? (
                <p>Loading emulations...</p>
            ) : (
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {emulations.length > 0 ? (
                            emulations.map((emu) => (
                                <tr key={emu.id}>
                                    <td>{emu.name}</td>
                                    <td>{emu.status}</td>
                                    <td>
                                        <button onClick={() => handleStopEmulation(emu.id)}>Stop</button>
                                        <button onClick={() => handleViewLogs(emu.id)}>View Logs</button>
                                        <button onClick={() => handleExportLogs(emu.id)}>Export Logs</button>
                                        <button onClick={() => setSelectedEmulation(emu)}>Select</button>
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan="3">No active emulations.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            )}

            <h2>Firmware Upload</h2>
            <input type="file" onChange={(e) => setFirmwareFile(e.target.files[0])} />
            <button onClick={handleFirmwareUpload} disabled={!firmwareFile}>Upload</button>

            <h2>Other Actions</h2>
            <button onClick={handleSetTimedEvent} disabled={!selectedEmulation}>
                Set Timed Event
            </button>
            <button onClick={handleEnableMirror} disabled={!selectedEmulation}>
                Enable UI Mirror
            </button>

            <h2>Logs</h2>
            <pre>{logs.length > 0 ? logs.join("\n") : "No logs available."}</pre>
        </div>
    );
};

export default EmulatorPanel;
