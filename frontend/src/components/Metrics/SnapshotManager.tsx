// src/components/Metrics/SnapshotManager.tsx
import React, { useEffect, useState } from "react";
import {
    listSnapshots,
    downloadSnapshot,
    deleteSnapshot,
    uploadFile,
    subscribeToFileEvents,
} from "@/services/fileService";
import type { SnapshotFile, FileEvent } from "@/types/fileTypes";
import "./SnapshotManager.css";

const SnapshotManager: React.FC = () => {
    const [snapshots, setSnapshots] = useState<string[]>([]);
    const [status, setStatus] = useState<Record<string, string>>({});

    useEffect(() => {
        loadSnapshots();
        const unsubscribe = subscribeToFileEvents((event: FileEvent) => {
            setStatus((prev) => ({ ...prev, [event.filename]: event.status }));
        });
        return () => unsubscribe();
    }, []);

    const loadSnapshots = async () => {
        const files = await listSnapshots();
        setSnapshots(files);
    };

    const handleDownload = async (filename: string) => {
        const blob = await downloadSnapshot(filename);
        if (blob) {
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
        }
    };

    const handleDelete = async (filename: string) => {
        await deleteSnapshot(filename);
        setSnapshots((prev) => prev.filter((f) => f !== filename));
    };

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            await uploadFile(file);
            loadSnapshots();
        }
    };

    return (
        <div className="snapshot-manager">
            <h2>Snapshot Manager</h2>

            <input type="file" onChange={handleFileUpload} />

            <ul>
                {snapshots.map((filename) => (
                    <li key={filename}>
                        <span>{filename}</span>
                        <small className="status">{status[filename] || "ready"}</small>
                        <div className="actions">
                            <button onClick={() => handleDownload(filename)}>Download</button>
                            <button onClick={() => handleDelete(filename)}>Delete</button>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default SnapshotManager;
