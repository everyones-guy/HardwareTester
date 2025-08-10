// src/services/mqttService.ts
import APIService from "@/services/apiService";
import { APIResponse } from "@/types/apiTypes";
import {
    MQTTPublishPayload,
    MQTTSubscribePayload,
    FirmwareUploadPayload,
    FirmwareValidationPayload,
    ProvisionPayload,
    RunTestsPayload,
    FirmwareUpdatePayload,
    SendRequestPayload,
} from "@/types/mqttTypes";

const BASE_PATH = "mqtt";

const MQTTService = {
    /**
     * Publish a message to an MQTT topic.
     */
    publish(payload: MQTTPublishPayload): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/publish`, "POST", payload);
    },

    /**
     * Subscribe to a topic.
     */
    subscribe(payload: MQTTSubscribePayload): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/subscribe`, "POST", payload);
    },

    /**
     * Send a request and wait for a response from a device.
     */
    sendRequest(payload: SendRequestPayload): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/request`, "POST", payload);
    },

    /**
     * Upload firmware to a device.
     */
    uploadFirmware(payload: FirmwareUploadPayload): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/firmware/upload`, "POST", payload);
    },

    /**
     * Trigger firmware validation on device.
     */
    validateFirmware(payload: FirmwareValidationPayload): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/firmware/validate`, "POST", payload);
    },

    /**
     * Check the status of a firmware update.
     */
    checkFirmwareStatus(deviceId: string): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/firmware/status/${deviceId}`, "GET");
    },

    /**
     * Push a firmware update URL to a device.
     */
    updateFirmware(payload: FirmwareUpdatePayload): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/firmware/update`, "POST", payload);
    },

    /**
     * Run a test plan on a specific device.
     */
    runTests(payload: RunTestsPayload): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/tests/run`, "POST", payload);
    },

    /**
     * Provision a device by updating firmware and running tests.
     */
    provisionDevice(payload: ProvisionPayload): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/provision`, "POST", payload);
    },
};

export default MQTTService;
