// src/services/firmwareService.ts
import APIService, { getWebSocketURL } from "@/services/apiService";
import { APIResponse } from "@/types/apiTypes";
import {
    FirmwareMeta,
    FirmwareComparisonResult,
    FirmwareProgressUpdate,
} from "@/types/firmwareTypes";

const BASE_PATH = "firmware";
export interface FirmwareTableEntry {
    id: string;
    name: string;
    version: string;
    deviceType: string;
    uploadDate: string;
}

/** Map FirmwareMeta[] into a table-friendly shape, defensively */
export async function listAsTableEntries(): Promise<FirmwareTableEntry[]> {
    const res = await FirmwareService.listFirmwareVersions();
    const list = (res as any)?.data?.firmwares ?? (res as any)?.firmwares ?? [];

    if (!Array.isArray(list)) return [];

    return list.map((f: any): FirmwareTableEntry => ({
        id: f.id ?? f._id ?? f.version ?? String(Math.random()),
        name: f.name ?? f.fileName ?? "Unknown",
        version: f.version ?? f.tag ?? "—",
        deviceType: f.deviceType ?? f.target ?? "—",
        uploadDate: f.uploadDate ?? f.createdAt ?? f.timestamp ?? new Date().toISOString(),
    }));
}

const FirmwareService = {
    /**
     * Get all available firmware versions.
     */
    listFirmwareVersions(): Promise<APIResponse<{ firmwares: FirmwareMeta[] }>> {
        return APIService.apiCall(`${BASE_PATH}/list`, "GET");
    },

    /**
     * Upload a new firmware binary (.bin, .hex, etc.)
     * @param file - Firmware file
     */
    uploadFirmware(file: File): Promise<APIResponse<{ message?: string }>> {
        const formData = new FormData();
        formData.append("firmware", file);
        return APIService.apiCall(`${BASE_PATH}/upload`, "POST", formData, {
            "Content-Type": "multipart/form-data",
        });
    },

    /**
     * Compare current firmware on device with latest available.
     * @param deviceId - Device ID to check
     */
    compareFirmwareVersion(deviceId: string): Promise<APIResponse<FirmwareComparisonResult>> {
        return APIService.apiCall(`${BASE_PATH}/compare/${deviceId}`, "GET");
    },

    /**
     * Deploy a firmware version to a device.
     * @param deviceId - Target device ID
     * @param firmwareId - Firmware ID or version string
     */
    deployFirmware(deviceId: string, firmwareId: string): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/deploy`, "POST", {
            deviceId,
            firmwareId,
        });
    },

    /**
     * Delete a firmware version by ID.
     * @param firmwareId - ID or version tag of the firmware
     */
    deleteFirmware(firmwareId: string): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/delete/${firmwareId}`, "DELETE");
    },

    /**
    * Download a firmware by ID.
    */
    async downloadFirmware(id: string, filename?: string): Promise<void> {
        const blob = await APIService.apiCall<Blob>(
            `${BASE_PATH}/download/${id}`,
            "GET",
            null,
            {},
            "blob"
        );
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", filename || `firmware_${id}.bin`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
    },

    /**
     * Subscribe to firmware deployment progress in real time.
     * @param deviceId - Device ID for the operation
     * @param callback - Called with update data
     * @returns Unsubscribe function
     */
    subscribeToFirmwareProgress(
        deviceId: string,
        callback: (update: FirmwareProgressUpdate) => void
    ): () => void {
        const socket = new WebSocket(getWebSocketURL(`${BASE_PATH}/progress/${deviceId}`));

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                callback(data);
            } catch (err) {
                console.error("Firmware progress WebSocket parse error:", err);
            }
        };

        socket.onerror = (err) => {
            console.error("Firmware WebSocket connection error:", err);
        };

        return () => socket.close();
    },
};

export default FirmwareService;
