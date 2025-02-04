import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:5000/api/hardware"; // Use environment variable

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
        return null; // Standardize error handling (always return null)
    }
};

/**
 * Fetches the list of available hardware devices.
 * @returns {Promise<Array>} List of devices or null if an error occurs.
 */
export const listDevices = async () => {
    const data = await apiRequest("list");
    return data?.devices || null; // Returns `null` on error instead of `[]`
};

/**
 * Fetches detailed information about a specific device.
 * @param {string} deviceId - The ID of the device.
 * @returns {Promise<Object|null>} Device details or null if an error occurs.
 */
export const getDeviceDetails = async (deviceId) => {
    const data = await apiRequest(`device/${deviceId}`);
    return data?.device || null;
};
