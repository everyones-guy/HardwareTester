import axios from "axios";

const API_BASE = "http://localhost:5000/api/emulator";

/**
 * Starts an emulation session for a specific device.
 * @param {Object} emulationData - Device emulation configuration.
 * @returns {Promise} - API response.
 */
export const startEmulation = async (emulationData) => {
    try {
        const response = await axios.post(`${API_BASE}/start`, emulationData);
        return response.data;
    } catch (error) {
        console.error("Error starting emulation:", error);
        throw error;
    }
};

/**
 * Stops a running emulation session.
 * @param {string} emulationId - ID of the emulation session.
 * @returns {Promise} - API response.
 */
export const stopEmulation = async (emulationId) => {
    try {
        const response = await axios.post(`${API_BASE}/stop`, { emulationId });
        return response.data;
    } catch (error) {
        console.error("Error stopping emulation:", error);
        throw error;
    }
};

/**
 * Fetches all active emulations.
 * @returns {Promise<Array>} - List of active emulations.
 */
export const getActiveEmulations = async () => {
    try {
        const response = await axios.get(`${API_BASE}/active`);
        return response.data;
    } catch (error) {
        console.error("Error fetching active emulations:", error);
        throw error;
    }
};

/**
 * Uploads firmware for validation.
 * @param {File} firmwareFile - The firmware file.
 * @returns {Promise} - Validation result.
 */
export const uploadFirmware = async (firmwareFile) => {
    const formData = new FormData();
    formData.append("file", firmwareFile);

    try {
        const response = await axios.post(`${API_BASE}/upload-firmware`, formData, {
            headers: { "Content-Type": "multipart/form-data" },
        });
        return response.data;
    } catch (error) {
        console.error("Error uploading firmware:", error);
        throw error;
    }
};

/**
 * Sets up a timed event trigger for an emulated device.
 * @param {string} emulationId - ID of the emulation session.
 * @param {Object} eventConfig - Configuration for the timed event.
 * @returns {Promise} - API response.
 */
export const setTimedEvent = async (emulationId, eventConfig) => {
    try {
        const response = await axios.post(`${API_BASE}/set-timed-event`, {
            emulationId,
            ...eventConfig,
        });
        return response.data;
    } catch (error) {
        console.error("Error setting timed event:", error);
        throw error;
    }
};

/**
 * Enables UI mirroring mode for an emulated touch controller.
 * @param {string} emulationId - ID of the emulation session.
 * @returns {Promise} - API response.
 */
export const enableUIMirror = async (emulationId) => {
    try {
        const response = await axios.post(`${API_BASE}/enable-mirror`, { emulationId });
        return response.data;
    } catch (error) {
        console.error("Error enabling UI mirroring:", error);
        throw error;
    }
};

/**
 * Fetches logs for a specific emulation session.
 * @param {string} emulationId - ID of the emulation session.
 * @returns {Promise<Array>} - List of logs.
 */
export const getEmulationLogs = async (emulationId) => {
    try {
        const response = await axios.get(`${API_BASE}/logs/${emulationId}`);
        return response.data;
    } catch (error) {
        console.error("Error fetching emulation logs:", error);
        throw error;
    }
};

/**
 * Exports logs for an emulation session.
 * @param {string} emulationId - ID of the emulation session.
 * @returns {Promise<Blob>} - Exported log file.
 */
export const exportLogs = async (emulationId) => {
    try {
        const response = await axios.get(`${API_BASE}/export-logs/${emulationId}`, {
            responseType: "blob",
        });
        return response.data;
    } catch (error) {
        console.error("Error exporting logs:", error);
        throw error;
    }
};
