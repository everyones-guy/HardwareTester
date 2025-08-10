// src/types/firmwareTypes.ts

/**
 * Represents metadata about a firmware file.
 */
export interface FirmwareMeta {
    id: string;
    name: string;
    version: string;
    uploadedAt: string; // ISO string
    uploadedBy: string;
    size: number; // in bytes
    type?: string; // "hex" | "bin" | etc.
}

/**
 * Represents the response from a firmware comparison.
 */
export interface FirmwareComparisonResult {
    deviceId: string;
    currentVersion: string;
    latestVersion: string;
    isUpToDate: boolean;
}

/**
 * Represents a firmware deployment request.
 */
export interface FirmwareDeployment {
    deviceId: string;
    firmwareId: string;
    scheduledAt?: string; // Optional ISO date for future deployment
}

/**
 * Real-time update payload received over WebSocket during deployment.
 */
export interface FirmwareProgressUpdate {
    firmwareId: string;
    deviceId: string;
    progress: number; // e.g., 0–100
    status: "pending" | "in_progress" | "completed" | "failed";
    message?: string;
}

export interface FirmwareUpdate {
    id: string;
    version: string;
    deviceId: string;
    status: string;
    progress: number;
};