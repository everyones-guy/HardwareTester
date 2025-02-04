import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:5000/api/emulator"; // Use environment variable

/**
 * Generic API request function to reduce duplication.
 * @param {string} endpoint - API endpoint
 * @param {Object} [options={}] - Axios options (method, headers, params, etc.)
 * @returns {Promise<any>} API response data
 */
const apiRequest = async (endpoint, options = {}) => {
    try {
        const response = await axios({ url: `${API_BASE}/${endpoint}`, ...options });
        return response.data;
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        throw error;
    }
};

/**
 * Starts an emulation session for a specific device.
 * @param {Object} emulationData - Device emulation configuration.
 */
export const startEmulation = (emulationData) =>
    apiRequest("start", { method: "POST", data: emulationData });

/**
 * Stops a running emulation session.
 * @param {string} emulationId - ID of the emulation session.
 */
export const stopEmulation = (emulationId) =>
    apiRequest("stop", { method: "POST", data: { emulationId } });

/**
 * Fetches all active emulations.
 */
export const getActiveEmulations = () => apiRequest("active");

/**
 * Uploads firmware for validation.
 * @param {File} firmwareFile - The firmware file.
 */
export const uploadFirmware = (firmwareFile) => {
    const formData = new FormData();
    formData.append("file", firmwareFile);

    return apiRequest("upload-firmware", {
        method: "POST",
        data: formData,
        headers: { "Content-Type": "multipart/form-data" },
    });
};

/**
 * Sets up a timed event trigger for an emulated device.
 * @param {string} emulationId - ID of the emulation session.
 * @param {Object} eventConfig - Configuration for the timed event.
 */
export const setTimedEvent = (emulationId, eventConfig) =>
    apiRequest("set-timed-event", { method: "POST", data: { emulationId, ...eventConfig } });

/**
 * Enables UI mirroring mode for an emulated touch controller.
 * @param {string} emulationId - ID of the emulation session.
 */
export const enableUIMirror = (emulationId) =>
    apiRequest("enable-mirror", { method: "POST", data: { emulationId } });

/**
 * Fetches logs for a specific emulation session.
 * @param {string} emulationId - ID of the emulation session.
 */
export const getEmulationLogs = (emulationId) => apiRequest(`logs/${emulationId}`);

/**
 * Exports logs for an emulation session.
 * @param {string} emulationId - ID of the emulation session.
 */
export const exportLogs = (emulationId) =>
    apiRequest(`export-logs/${emulationId}`, { responseType: "blob" });
