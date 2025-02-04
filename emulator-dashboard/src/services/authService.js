import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:5000/api/auth";
const TOKEN_STORAGE = sessionStorage; // Change to localStorage for persistent login

/**
 * Saves authentication tokens.
 * @param {string} token - JWT access token.
 */
const saveAuthToken = (token) => {
    TOKEN_STORAGE.setItem("authToken", token);
};

/**
 * Retrieves the current authentication token.
 * @returns {string|null} The stored auth token.
 */
const getAuthToken = () => {
    return TOKEN_STORAGE.getItem("authToken");
};

/**
 * Removes authentication token.
 */
const clearAuthToken = () => {
    TOKEN_STORAGE.removeItem("authToken");
};

/**
 * Logs in a user and stores their token.
 * @param {string} email - User email.
 * @param {string} password - User password.
 * @returns {Promise<Object>} User data or error.
 */
export const loginUser = async (email, password) => {
    try {
        const response = await axios.post(`${API_BASE}/login`, { email, password });
        saveAuthToken(response.data.token); // Store token in sessionStorage
        return response.data;
    } catch (error) {
        console.error("Error logging in:", error);
        return { error: "Login failed." };
    }
};

/**
 * Logs out the current user.
 */
export const logoutUser = async () => {
    try {
        await axios.post(`${API_BASE}/logout`);
        clearAuthToken(); // Remove token on logout
    } catch (error) {
        console.error("Error logging out:", error);
    }
};

/**
 * Fetches the currently logged-in user's profile.
 * @returns {Promise<Object|null>} User profile or null if not logged in.
 */
export const getUserProfile = async () => {
    try {
        const token = getAuthToken(); // Retrieve stored token
        if (!token) return null; // Prevents unnecessary API calls

        const response = await axios.get(`${API_BASE}/profile`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        return response.data;
    } catch (error) {
        console.error("Error fetching user profile:", error);
        return null;
    }
};

/**
 * Refreshes the authentication token if expired.
 * @returns {Promise<string|null>} New token or null if refresh fails.
 */
export const refreshAuthToken = async () => {
    try {
        const response = await axios.post(`${API_BASE}/refresh-token`);
        saveAuthToken(response.data.token);
        return response.data.token;
    } catch (error) {
        console.error("Error refreshing auth token:", error);
        clearAuthToken();
        return null;
    }
};

/**
 * Axios interceptor to automatically attach auth token to requests.
 */
axios.interceptors.request.use(
    async (config) => {
        const token = getAuthToken();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);
