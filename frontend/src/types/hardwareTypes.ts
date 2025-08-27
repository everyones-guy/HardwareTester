// src/types/hardwareTypes.ts

export interface DeviceInfo {
    id: number;
    name: string;
    model: string;
    status: string;
    metadata: Record<string, any>;
}

export interface DeviceStatus {
    id: number;
    name: string;
    firmware_version: string;
    metadata: Record<string, any>;
}

export interface FirmwareMetadata {
    length: number;
    lines: number;
    checksum: string;
}

export interface FirmwareHistoryEntry {
    firmware_id: number;
    hash: string;
    version: string;
    uploaded_at: string;
    uploaded_by: string;
}

export interface ControllerInfo {
    id: number;
    name: string;
    firmware_version: string;
    available: boolean;
}

export interface PeripheralInfo {
    id: number;
    name: string;
    type: string;
    properties: Record<string, any>;
}

export interface DeviceDetails {
    id: number;
    device_id: string;
    name: string;
    firmware_version: string;
    device_metadata: Record<string, any>;
    created_at: string;
    updated_at: string;
    created_by: string;
    modified_by: string;
    firmware_history: FirmwareHistoryEntry[];
    controllers: ControllerInfo[];
    peripherals: PeripheralInfo[];
}

export interface LinkInfo {
    id: number;
    source_id: number;
    target_id: number;
    metadata: Record<string, any>;
}

export interface SaveLinkPayload {
    source_id: number;
    target_id: number;
    metadata?: Record<string, any>;
}

export interface UploadFirmwarePayload {
    firmware_data: string;
}

export interface StoreFirmwarePayload {
    firmware_hash: string;
    firmware_data: string;
}

export interface TrackFirmwarePayload {
    device_id: number;
    firmware_id: number;
}

// -----------------------------
// Extended Discovery Types
// -----------------------------
export type Transport = "usb" | "bluetooth" | "wifi" | "ethernet";

export interface Device {
    id: string;
    name: string;
    transport: Transport;
    vendor?: string;
    product?: string;
    address?: string;
    port?: number;
    serial?: string;
    firmwareVersion?: string;
    lastSeen?: string;
    status?: "online" | "offline" | "unknown";
    tags?: string[];
}

export interface DiscoverResponse {
    devices: Device[];
    scanId: string;
    startedAt: string;
}
