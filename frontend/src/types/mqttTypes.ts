// src/types/mqttTypes.ts

/**
 * Payload for publishing an MQTT message
 */
export interface MQTTPublishPayload {
    topic: string;
    payload: Record<string, any> | string;
}

/**
 * Payload for subscribing to an MQTT topic
 */
export interface MQTTSubscribePayload {
    topic: string;
}

/**
 * Payload for sending a request and waiting for MQTT response
 */
export interface SendRequestPayload {
    topic: string;
    payload: Record<string, any>;
    response_topic: string;
    timeout?: number; // in seconds
}

/**
 * Payload for uploading firmware (chunked or full)
 */
export interface FirmwareUploadPayload {
    device_id: string;
    path: string; // absolute or relative firmware file path
}

/**
 * Payload for triggering firmware validation
 */
export interface FirmwareValidationPayload {
    device_id: string;
}

/**
 * Payload for pushing a firmware update via URL
 */
export interface FirmwareUpdatePayload {
    device_id: string;
    firmware_url: string;
}

/**
 * Payload for test execution request
 */
export interface RunTestsPayload {
    device_id: string;
    test_plan: Record<string, any>;
}

/**
 * Combined payload for provisioning a device
 */
export interface ProvisionPayload {
    device_id: string;
    firmware_url: string;
    test_plan: Record<string, any>;
}
