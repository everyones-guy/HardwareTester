// src/components/EmulatorDashboard/EmulatorPanel.tsx
import React, { useEffect, useState } from "react";
import EmulatorService from "@/services/emulatorApiService";
import { EmulationSession, EmulatorLogEntry } from "@/types/emulatorTypes";
import "./EmulatorPanel.css";

const EmulatorPanel: React.FC = () => {
    const [emulations, setEmulations] = useState<EmulationSession[]>([]);
    const [firmwareFile, setFirmwareFile] = useState<File | null>(null);
    const [selectedEmulation, setSelectedEmulation] = useState<EmulationSession | null>(null);
    const [logs, setLogs] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const unwrapList = (res: any): EmulationSession[] =>
        res?.data?.emulations ?? res?.emulations ?? (Array.isArray(res) ? res : []);

    const loadEmulations = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await EmulatorService.listActiveEmulations();
            setEmulations(unwrapList(res));
        } catch (err: any) {
            console.error("Error loading emulations:", err);
            setError(err?.message || "Failed to load emulations.");
            setEmulations([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadEmulations();
    }, []);

    const handleStartEmulation = async () => {
        try {
            setLoading(true);
            // TODO: replace with real machine/blueprint selections
            await EmulatorService.startEmulation("MyMachine", "MyBlueprint", false);
            await loadEmulations();
        } catch (err: any) {
            console.error("Error starting emulation:", err);
            setError(err?.message || "Failed to start emulation.");
        } finally {
            setLoading(false);
        }
    };

    const handleStopEmulation = async (machine_name: string) => {
        try {
            await EmulatorService.stopEmulation(machine_name);
            await loadEmulations();
        } catch (err: any) {
            console.error("Error stopping emulation:", err);
            setError(err?.message || "Failed to stop emulation.");
        }
    };

    const handleFirmwareUpload = async () => {
        if (!firmwareFile) return alert("Please select a firmware file.");
        try {
            const formData = new FormData();
            formData.append("file", firmwareFile);
            await EmulatorService.uploadBlueprintFile(formData);
            alert("Firmware uploaded successfully!");
            setFirmwareFile(null);
        } catch (err: any) {
            console.error("Error uploading firmware:", err);
            setError(err?.message || "Firmware upload failed.");
        }
    };

    const handleSetTimedEvent = async () => {
        if (!selectedEmulation) return alert("Select an emulation first.");
        try {
            // Try to use a session id if present, fall back to machine name
            const sessionKey =
                (selectedEmulation as any).session_id ??
                (selectedEmulation as any).id ??
                selectedEmulation.machine_name;

            await EmulatorService.addOrUpdatePeripherals(sessionKey, [
                {
                    name: "Timer",
                    type: "event",
                    properties: {
                        trigger: "future",
                        at: Date.now() + 60_000, // +1 minute
                    },
                },
            ]);
            alert("Timed event set!");
        } catch (err: any) {
            console.error("Error setting timed event:", err);
            setError(err?.message || "Failed to set timed event.");
        }
    };

    const handleEnableMirror = async () => {
        if (!selectedEmulation) return alert("Select an emulation first.");
        try {
            // Replace with your actual mirror blueprint path or payload
            await EmulatorService.loadBlueprintFromFile("/path/to/mirror.yaml");
            alert("UI Mirror enabled!");
        } catch (err: any) {
            console.error("Error enabling UI mirror:", err);
            setError(err?.message || "Failed to enable UI mirror.");
        }
    };

    const handleViewLogs = async () => {
        try {
            const res = await EmulatorService.getLogs();
            const entries: EmulatorLogEntry[] = res?.data?.logs ?? res?.logs ?? [];
            const formatted = Array.isArray(entries)
                ? entries.map((l) => `[${l.timestamp}] ${l.message}`)
                : [];
            setLogs(formatted);
        } catch (err: any) {
            console.error("Error fetching logs:", err);
            setError(err?.message || "Failed to fetch logs.");
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
                            <th>Machine</th>
                            <th>Blueprint</th>
                            <th>Started</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {emulations.length > 0 ? (
                            emulations.map((emu) => (
                                <tr key={`${emu.machine_name}-${emu.start_time}`}>
                                    <td>{emu.machine_name}</td>
                                    <td>{emu.blueprint}</td>
                                    <td>{emu.start_time ? new Date(emu.start_time).toLocaleString() : "-"}</td>
                                    <td>
                                        <button onClick={() => handleStopEmulation(emu.machine_name)}>Stop</button>
                                        <button onClick={handleViewLogs}>View Logs</button>
                                        <button onClick={() => setSelectedEmulation(emu)}>Select</button>
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={4}>No active emulations.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            )}

            <h2>Firmware Upload</h2>
            <input type="file" onChange={(e) => setFirmwareFile(e.target.files?.[0] || null)} />
            <button onClick={handleFirmwareUpload} disabled={!firmwareFile}>
                Upload
            </button>

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
