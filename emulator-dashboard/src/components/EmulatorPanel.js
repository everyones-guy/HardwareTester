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

    useEffect(() => {
        loadEmulations();
    }, []);

    const loadEmulations = async () => {
        const data = await getActiveEmulations();
        setEmulations(data);
    };

    const handleStartEmulation = async () => {
        const emulationData = {
            deviceType: "CustomDevice",
            firmwareVersion: "1.0.0",
        };
        await startEmulation(emulationData);
        loadEmulations();
    };

    const handleStopEmulation = async (emulationId) => {
        await stopEmulation(emulationId);
        loadEmulations();
    };

    const handleFirmwareUpload = async () => {
        if (!firmwareFile) return;
        await uploadFirmware(firmwareFile);
    };

    const handleSetTimedEvent = async () => {
        if (!selectedEmulation) return;
        const eventConfig = {
            eventType: "trigger-action",
            triggerTime: Date.now() + 60000,
        };
        await setTimedEvent(selectedEmulation.id, eventConfig);
    };

    const handleEnableMirror = async () => {
        if (!selectedEmulation) return;
        await enableUIMirror(selectedEmulation.id);
    };

    const handleViewLogs = async (emulationId) => {
        const data = await getEmulationLogs(emulationId);
        setLogs(data);
    };

    const handleExportLogs = async (emulationId) => {
        const data = await exportLogs(emulationId);
        const url = window.URL.createObjectURL(new Blob([data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", `emulation_logs_${emulationId}.txt`);
        document.body.appendChild(link);
        link.click();
    };

    return (
        <div className="emulator-panel">
            <h1>Emulator Dashboard</h1>

            <button onClick={handleStartEmulation}>Start New Emulation</button>

            <h2>Active Emulations</h2>
            <ul>
                {emulations.map((emu) => (
                    <li key={emu.id}>
                        {emu.name} - {emu.status}
                        <button onClick={() => handleStopEmulation(emu.id)}>Stop</button>
                        <button onClick={() => handleViewLogs(emu.id)}>View Logs</button>
                        <button onClick={() => handleExportLogs(emu.id)}>Export Logs</button>
                    </li>
                ))}
            </ul>

            <h2>Firmware Upload</h2>
            <input type="file" onChange={(e) => setFirmwareFile(e.target.files[0])} />
            <button onClick={handleFirmwareUpload}>Upload</button>

            <h2>Other Actions</h2>
            <button onClick={handleSetTimedEvent}>Set Timed Event</button>
            <button onClick={handleEnableMirror}>Enable UI Mirror</button>

            <h2>Logs</h2>
            <pre>{logs.join("\n")}</pre>
        </div>
    );
};

export default EmulatorPanel;
