import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:5000/api/serial"; // Use environment variable

/**
 * Generic API request function to reduce duplication.
 * @param {string} endpoint - API endpoint
 * @param {Object} [options={}] - Axios options (method, headers, params, etc.)
 * @returns {Promise<any>} API response data or error object
 */
const apiRequest = async (endpoint, options = {}) => {
    try {
        const response = await axios({ url: `${API_BASE}/${endpoint}`, ...options });
        return response.data;
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        return { error: `Failed to execute request for ${endpoint}.` }; // Standardize error handling
    }
};

/**
 * Lists available serial ports.
 * @returns {Promise<Array>} List of available serial ports.
 */
export const listSerialPorts = () => apiRequest("ports");

/**
 * Connects to a serial port.
 * @param {string} port - Serial port name.
 * @param {number} baudrate - Baud rate for the connection.
 * @returns {Promise<Object>} Connection status or error.
 */
export const connectSerial = (port, baudrate) =>
    apiRequest("connect", { method: "POST", data: { port, baudrate } });

/**
 * Sends data over the serial connection.
 * @param {string} data - Data to send.
 * @returns {Promise<Object>} Acknowledgment or error.
 */
export const sendSerialData = (data) =>
    apiRequest("send", { method: "POST", data: { data } });

/**
 * Disconnects from the serial port.
 * @returns {Promise<Object>} Disconnection status or error.
 */
export const disconnectSerial = () => apiRequest("disconnect", { method: "POST" });
