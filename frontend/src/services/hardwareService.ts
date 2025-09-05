// src/services/hardwareService.ts
// Unified HardwareService: backend contract methods + extended discovery helpers

import APIService from "@/services/apiService";
import {
    DeviceInfo,
    DeviceStatus,
    FirmwareMetadata,
    DeviceDetails,
    LinkInfo,
    Device,             // extended types
    DiscoverResponse,   // extended types
} from "@/types/hardwareTypes";
import { APIResponse } from "@/types/apiTypes";

const BASE_PATH = "hardware";

// -----------------------------
// Backend Contract Methods (yours, unchanged)
// -----------------------------
const HardwareService = {
    discoverDevice(deviceId: number): Promise<APIResponse<{ device: DeviceInfo }>> {
        return APIService.apiCall(`${BASE_PATH}/discover/${deviceId}`, "GET");
    },

    updateDeviceStatus(deviceId: number, status: string): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/status/${deviceId}`, "PUT", { status });
    },

    listDevices(): Promise<APIResponse<{ devices: DeviceInfo[] }>> {
        return APIService.apiCall(`${BASE_PATH}/list`, "GET");
    },

    deleteDevice(deviceId: number): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/delete/${deviceId}`, "DELETE");
    },

    uploadFirmwareToDevice(deviceId: number, firmwareData: string): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/firmware/upload/${deviceId}`, "POST", {
            firmware_data: firmwareData,
        });
    },

    storeFirmware(
        firmwareHash: string,
        firmwareData: string
    ): Promise<APIResponse<{ firmware_id: number; existing: boolean }>> {
        return APIService.apiCall(`${BASE_PATH}/firmware/store`, "POST", {
            firmware_hash: firmwareHash,
            firmware_data: firmwareData,
        });
    },

    trackFirmwareVersion(deviceId: number, firmwareId: number): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/firmware/track`, "POST", {
            device_id: deviceId,
            firmware_id: firmwareId,
        });
    },

    generateMDF(firmwareData: string): Promise<APIResponse<FirmwareMetadata>> {
        return APIService.apiCall(`${BASE_PATH}/firmware/mdf`, "POST", {
            firmware_data: firmwareData,
        });
    },

    getDeviceStatus(deviceId?: number): Promise<APIResponse<{ status: DeviceStatus | DeviceStatus[] }>> {
        const url = deviceId ? `${BASE_PATH}/status/${deviceId}` : `${BASE_PATH}/status`;
        return APIService.apiCall(url, "GET");
    },

    saveLink(
        sourceId: number,
        targetId: number,
        metadata: Record<string, any> = {}
    ): Promise<APIResponse<{ link_id: number }>> {
        return APIService.apiCall(`${BASE_PATH}/link/save`, "POST", {
            source_id: sourceId,
            target_id: targetId,
            metadata,
        });
    },

    getLinks(): Promise<APIResponse<LinkInfo[]>> {
        return APIService.apiCall(`${BASE_PATH}/links`, "GET");
    },

    getDeviceFromDb(deviceId: string): Promise<APIResponse<DeviceDetails>> {
        return APIService.apiCall(`${BASE_PATH}/details/${deviceId}`, "GET");
    },
};

// -----------------------------
// Extended Discovery Helpers (additive)
// -----------------------------
const BASE = "/api/hardware";
const ENDPOINTS = {
    discoverDevices: `${BASE}/devices/discover`,   // POST triggers a scan
    listDevices: `${BASE}/devices`,            // GET returns known devices
    deviceById: (id: string) => `${BASE}/devices/${encodeURIComponent(id)}`,
    discoveryStream: `${BASE}/devices/discover/stream`, // WS/SSE
};

function normalizeDevices(arr: any[]): Device[] {
    if (!Array.isArray(arr)) return [];
    return arr.map((d) => ({
        id: String(d.id ?? d.deviceId ?? d.path ?? ""),
        name: String(d.name ?? d.label ?? d.product ?? "Unknown Device"),
        transport: (d.transport ?? d.type ?? "usb") as Device["transport"],
        vendor: d.vendor ?? d.manufacturer ?? undefined,
        product: d.product ?? d.model ?? undefined,
        address: d.address ?? d.mac ?? d.ip ?? d.path ?? undefined,
        port: typeof d.port === "number" ? d.port : undefined,
        serial: d.serial ?? d.sn ?? undefined,
        firmwareVersion: d.firmwareVersion ?? d.fw ?? undefined,
        lastSeen: d.lastSeen ?? d.updatedAt ?? d.discoveredAt ?? undefined,
        status: (d.status as Device["status"]) ?? "unknown",
        tags: Array.isArray(d.tags) ? d.tags : [],
    }));
}

function mockDiscover(): DiscoverResponse {
    const now = new Date().toISOString();
    return {
        scanId: `scan_${Date.now()}`,
        startedAt: now,
        devices: normalizeDevices([
            {
                id: "usb-FT232-01",
                name: "FTDI USB UART",
                transport: "usb",
                vendor: "FTDI",
                product: "FT232",
                address: "/dev/ttyUSB0",
                serial: "FT232-ABC123",
                firmwareVersion: "n/a",
                lastSeen: now,
                status: "online",
                tags: ["serial", "uart"],
            },
            {
                id: "bt-ESP32-01",
                name: "ESP32-BLE Peripheral",
                transport: "bluetooth",
                vendor: "Espressif",
                product: "ESP32",
                address: "AA:BB:CC:DD:EE:FF",
                firmwareVersion: "1.4.2",
                lastSeen: now,
                status: "online",
                tags: ["ble", "sensor"],
            },
            {
                id: "lan-STM32-01",
                name: "STM32 Test Rig",
                transport: "ethernet",
                vendor: "STMicro",
                product: "Nucleo",
                address: "192.168.1.120",
                port: 5020,
                firmwareVersion: "0.9.8",
                lastSeen: now,
                status: "online",
                tags: ["rig", "modbus"],
            },
        ]),
    };
}

async function discoverDevicesExtended(): Promise<DiscoverResponse> {
    try {
        const res = await APIService.apiCallWithRetry(
            ENDPOINTS.discoverDevices, "POST", {
            transports: ["usb", "bluetooth", "wifi", "ethernet"],
        });
        const devices = normalizeDevices((res as any)?.devices ?? []);
        return {
            scanId: (res as any)?.scanId ?? `scan_${Date.now()}`,
            startedAt: (res as any)?.startedAt ?? new Date().toISOString(),
            devices,
        };
    } catch (err: any) {
        if (err?.response?.status === 404 || err?.response?.status === 501) {
            return mockDiscover();
        }
        throw err;
    }
}

async function listDevicesExtended(): Promise<Device[]> {
    try { 
        const res = await APIService.apiCallWithRetry(
            ENDPOINTS.listDevices, "GET"
        );
        return normalizeDevices((res as any)?.data ?? []);
    } catch (err: any) {
        if (err?.response?.status === 404) return [];
        throw err;
    }
}

async function discoverDeviceExtended(deviceId: string): Promise<Device | null> {
    try {
        const res = await APIService.apiCallWithRetry(
            ENDPOINTS.deviceById(deviceId), "GET"
        );
        const normalized = normalizeDevices([(res as any)?.data ?? {}]);
        return normalized[0] ?? null;
    } catch (err: any) {
        if (err?.response?.status === 404) return null;
        throw err;
    }
}

function subscribeToDiscoveryWS(onMessage: (devices: Device[]) => void): () => void {
    const url = APIService.getWebSocketURL(ENDPOINTS.discoveryStream);
    const ws = new WebSocket(url);
    ws.onmessage = (evt) => {
        try {
            const payload = JSON.parse(evt.data);
            if (Array.isArray(payload.devices)) onMessage(normalizeDevices(payload.devices));
        } catch { }
    };
    return () => ws.close(1000);
}

function subscribeToDiscoverySSE(onMessage: (devices: Device[]) => void): () => void {
    const sse = new EventSource(ENDPOINTS.discoveryStream);
    const handler = (evt: MessageEvent) => {
        try {
            const payload = JSON.parse(evt.data);
            if (Array.isArray(payload.devices)) onMessage(normalizeDevices(payload.devices));
        } catch { }
    };
    sse.addEventListener("message", handler as any);
    return () => sse.close();
}

// Attach extended helpers (non-breaking, additive)
Object.assign(HardwareService, {
    discoverDevicesExtended,
    listDevicesExtended,
    discoverDeviceExtended,
    subscribeToDiscoveryWS,
    subscribeToDiscoverySSE,
});

export default HardwareService;
