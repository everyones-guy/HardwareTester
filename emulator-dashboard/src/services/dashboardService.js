import axios from "axios";

const API_BASE = "http://localhost:5000/api/dashboard";

/**
 * Fetches full dashboard metrics including active emulations, system health, and logs.
 * @returns {Promise<Object>} Dashboard data
 */
export const getDashboardData = async () => {
    try {
        const response = await axios.get(`${API_BASE}/metrics`);
        return response.data;
    } catch (error) {
        console.error("Error fetching dashboard data:", error);
        throw error;
    }
};

/**
 * Fetches system status including CPU, memory, and network information.
 * @returns {Promise<Object>} System health data
 */
export const getSystemStatus = async () => {
    try {
        const response = await axios.get(`${API_BASE}/system-status`);
        return response.data;
    } catch (error) {
        console.error("Error fetching system status:", error);
        throw error;
    }
};

/**
 * Fetches currently active emulations.
 * @returns {Promise<Array>} List of active emulations
 */
export const getActiveEmulations = async () => {
    try {
        const response = await axios.get(`${API_BASE}/active-emulations`);
        return response.data;
    } catch (error) {
        console.error("Error fetching active emulations:", error);
        throw error;
    }
};

/**
 * Fetches detailed logs for a specific emulation session.
 * @param {string} emulationId - The ID of the emulation session.
 * @returns {Promise<Array>} List of logs
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
 * Fetches error reports and system diagnostics.
 * @returns {Promise<Array>} List of recent errors and diagnostics
 */
export const getErrorReports = async () => {
    try {
        const response = await axios.get(`${API_BASE}/error-reports`);
        return response.data;
    } catch (error) {
        console.error("Error fetching error reports:", error);
        throw error;
    }
};

/**
 * Fetches specific test metrics related to hardware testing.
 * @returns {Promise<Array>} Test execution results and reports
 */
export const getTestMetrics = async () => {
    try {
        const response = await axios.get(`${API_BASE}/test-metrics`);
        return response.data;
    } catch (error) {
        console.error("Error fetching test metrics:", error);
        throw error;
    }
};

/**
 * Exports dashboard logs for analysis.
 * @returns {Promise<Blob>} Log file
 */
export const exportDashboardLogs = async () => {
    try {
        const response = await axios.get(`${API_BASE}/export-logs`, {
            responseType: "blob",
        });
        return response.data;
    } catch (error) {
        console.error("Error exporting logs:", error);
        throw error;
    }
};

/**
 * Fetches custom analytics based on user-defined widgets.
 * @param {string} widgetId - ID of the custom widget.
 * @returns {Promise<Object>} Custom analytics data
 */
export const getCustomWidgetData = async (widgetId) => {
    try {
        const response = await axios.get(`${API_BASE}/custom-widget/${widgetId}`);
        return response.data;
    } catch (error) {
        console.error("Error fetching custom widget data:", error);
        throw error;
    }
};
