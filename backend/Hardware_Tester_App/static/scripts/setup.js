// setup.js for the browser
globalThis.$ = globalThis.jQuery = jQuery;

import axios from "axios";

// Utility function for API calls using axios
globalThis.apiCall = async function (endpoint, method = "GET", data = {}) {
    try {
        const csrfMetaTag = document.querySelector('meta[name="csrf-token"]');
        const csrfToken = csrfMetaTag ? csrfMetaTag.content : null; // Prevents errors if missing

        const headers = {};
        if (csrfToken) {
            headers["X-CSRFToken"] = csrfToken; // Attaches CSRF token if available
        }

        const response = await axios({
            url: endpoint,
            method: method.toUpperCase(),
            headers: headers,
            data: ["GET", "DELETE"].includes(method.toUpperCase()) ? undefined : data, // Ensures GET/DELETE don't send bodies
        });

        return response.data; // Resolves with API response

    } catch (error) {
        console.error(`API Error (${method} ${endpoint}):`, error.response?.data?.error || error.message);
        throw error.response?.data || { error: "An unknown error occurred." }; // Throws error so it can be caught
    }
};
