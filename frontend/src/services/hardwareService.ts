// src/services/hardwareService.ts
import APIService from "@/services/apiService";
import {
    DeviceInfo,
    DeviceStatus,
    FirmwareMetadata,
    DeviceDetails,
    LinkInfo,
} from "@/types/hardwareTypes";
import { APIResponse } from "@/types/apiTypes";

const BASE_PATH = "hardware";

const HardwareService = {
    /**
     * Discover a single device by ID.
     */
    discoverDevice(deviceId: number): Promise<APIResponse<{ device: DeviceInfo }>> {
        return APIService.apiCall(`${BASE_PATH}/discover/${deviceId}`, "GET");
    },

    /**
     * Update device status (e.g. online, offline, maintenance).
     */
    updateDeviceStatus(deviceId: number, status: string): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/status/${deviceId}`, "PUT", { status });
    },

    /**
     * Retrieve a list of all devices.
     */
    listDevices(): Promise<APIResponse<{ devices: DeviceInfo[] }>> {
        return APIService.apiCall(`${BASE_PATH}/list`, "GET");
    },

    /**
     * Delete a specific device by ID.
     */
    deleteDevice(deviceId: number): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/delete/${deviceId}`, "DELETE");
    },

    /**
     * Upload firmware (as text) to a device.
     */
    uploadFirmwareToDevice(deviceId: number, firmwareData: string): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/firmware/upload/${deviceId}`, "POST", {
            firmware_data: firmwareData,
        });
    },

    /**
     * Store a firmware blob in the database.
     */
    storeFirmware(firmwareHash: string, firmwareData: string): Promise<APIResponse<{ firmware_id: number; existing: boolean }>> {
        return APIService.apiCall(`${BASE_PATH}/firmware/store`, "POST", {
            firmware_hash: firmwareHash,
            firmware_data: firmwareData,
        });
    },

    /**
     * Track a firmware version assigned to a device.
     */
    trackFirmwareVersion(deviceId: number, firmwareId: number): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/firmware/track`, "POST", {
            device_id: deviceId,
            firmware_id: firmwareId,
        });
    },

    /**
     * Generate a Master Data File (MDF) from firmware content.
     */
    generateMDF(firmwareData: string): Promise<APIResponse<FirmwareMetadata>> {
        return APIService.apiCall(`${BASE_PATH}/firmware/mdf`, "POST", {
            firmware_data: firmwareData,
        });
    },

    /**
     * Retrieve status for a specific device, or all devices.
     */
    getDeviceStatus(deviceId?: number): Promise<APIResponse<{ status: DeviceStatus | DeviceStatus[] }>> {
        const url = deviceId ? `${BASE_PATH}/status/${deviceId}` : `${BASE_PATH}/status`;
        return APIService.apiCall(url, "GET");
    },

    /**
     * Create a link between two devices.
     */
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

    /**
     * Retrieve all stored hardware links.
     */
    getLinks(): Promise<APIResponse<LinkInfo[]>> {
        return APIService.apiCall(`${BASE_PATH}/links`, "GET");
    },

    /**
     * Fetch detailed device info including firmware history, controllers, and peripherals.
     */
    getDeviceFromDb(deviceId: string): Promise<APIResponse<DeviceDetails>> {
        return APIService.apiCall(`${BASE_PATH}/details/${deviceId}`, "GET");
    },
};

export default HardwareService;
