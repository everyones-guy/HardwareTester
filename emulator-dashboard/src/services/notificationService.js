import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:5000/api/notifications";

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
        return { error: `Failed to execute request for ${endpoint}.` }; // Standardized error handling
    }
};

/**
 * Fetches recent notifications.
 * @returns {Promise<Array>} List of notifications or error object.
 */
export const getNotifications = () => apiRequest("list");

/**
 * Marks a notification as read.
 * @param {string} notificationId - The notification ID.
 * @returns {Promise<Object>} Updated notification status or error object.
 */
export const markNotificationAsRead = (notificationId) =>
    apiRequest(`mark-read/${notificationId}`, { method: "POST" });

/**
 * Deletes a notification.
 * @param {string} notificationId - The notification ID.
 * @returns {Promise<Object>} Deletion status or error object.
 */
export const deleteNotification = (notificationId) =>
    apiRequest(`delete/${notificationId}`, { method: "DELETE" });

/**
 * Subscribes to real-time notifications via WebSocket.
 * @param {Function} callback - Function to execute when a new notification is received.
 */
export const subscribeToNotifications = (callback) => {
    const socket = new WebSocket(`${API_BASE.replace("http", "ws")}/live`);

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        callback(data);
    };

    socket.onerror = (error) => console.error("WebSocket error:", error);

    return () => socket.close(); // Cleanup function to close WebSocket
};
