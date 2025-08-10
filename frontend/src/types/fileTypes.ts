// src/types/fileTypes.ts

export interface SnapshotFile {
    name: string;
    size: number;
    createdAt: string;
    type: "log" | "snapshot" | "json" | "config";
}

export interface FileUploadResult {
    filename: string;
    path: string;
    uploadedAt: string;
    success: boolean;
    message?: string;
}

export interface FileEvent {
    filename: string;
    status: "processing" | "ready" | "error";
    timestamp: string;
    details?: string;
}
