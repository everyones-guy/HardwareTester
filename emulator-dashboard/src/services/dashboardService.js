import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:5000/dashboard"; // Use environment variable

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
        return null; // Standardized error handling
    }
};

/** ==========================
 *  Standard API Requests
 *  ========================== */

/**
 * Fetches full dashboard metrics including active emulations, system health, and logs.
 */
export const getDashboardData = () => apiRequest("metrics");

/**
 * Fetches system status including CPU, memory, and network information.
 */
export const getSystemStatus = () => apiRequest("system-status");

/**
 * Fetches currently active emulations.
 */
export const getActiveEmulations = () => apiRequest("active-emulations");

/**
 * Fetches detailed logs for a specific emulation session.
 * @param {string} emulationId - The ID of the emulation session.
 */
export const getEmulationLogs = (emulationId) => apiRequest(`logs/${emulationId}`);

/**
 * Fetches error reports and system diagnostics.
 */
export const getErrorReports = () => apiRequest("error-reports");

/**
 * Fetches specific test metrics related to hardware testing.
 */
export const getTestMetrics = () => apiRequest("test-metrics");

/**
 * Exports dashboard logs for analysis.
 * @returns {Promise<Blob>} Log file
 */
export const exportDashboardLogs = () =>
    apiRequest("export-logs", { responseType: "blob" });

/**
 * Fetches custom analytics based on user-defined widgets.
 * @param {string} widgetId - ID of the custom widget.
 */
export const getCustomWidgetData = (widgetId) => apiRequest(`custom-widget/${widgetId}`);

/** ==========================
 *  WebSocket-Based Live Updates
 *  ========================== */

/**
 * WebSocket-based real-time monitoring for system health.
 * @param {Function} callback - Function to handle real-time system updates.
 */
export const subscribeToSystemHealth = (callback) => {
    const socket = new WebSocket(`${API_BASE.replace("http", "ws")}/system-health`);

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        callback(data);
    };

    socket.onerror = (error) => console.error("WebSocket error:", error);

    return () => socket.close(); // Cleanup function to close WebSocket
};

/**
 * WebSocket-based real-time test metric updates.
 * @param {Function} callback - Function to handle test results in real time.
 */
export const subscribeToTestMetrics = (callback) => {
    const socket = new WebSocket(`${API_BASE.replace("http", "ws")}/test-metrics`);

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        callback(data);
    };

    socket.onerror = (error) => console.error("WebSocket error:", error);

    return () => socket.close(); // Cleanup function to close WebSocket
};
