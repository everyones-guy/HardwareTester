// src/services/settingsService.ts
import APIService from "@/services/apiService";
import { APIResponse } from "@/types/apiTypes";

const BASE_PATH = "settings";

const SettingsService = {
    /** ============================
     *  Global Application Settings
     *  ============================ */

    /**
     * Fetch global settings.
     */
    getGlobalSettings(): Promise<APIResponse<{ settings: Record<string, any> }>> {
        return APIService.apiCall(`${BASE_PATH}/global`, "GET");
    },

    /**
     * Update global app settings.
     * @param settings - Partial update object
     */
    updateGlobalSettings(settings: Record<string, any>): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/global`, "POST", settings);
    },

    /** ============================
     *  Hostname Configuration
     *  ============================ */

    /**
     * Fetch the hostname of the current system.
     */
    getHostname(): Promise<APIResponse<{ hostname: string }>> {
        return APIService.apiCall(`${BASE_PATH}/hostname`, "GET");
    },

    /**
     * Set or update the device/server hostname.
     * @param hostname - New hostname string
     */
    setHostname(hostname: string): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/hostname`, "POST", { hostname });
    },

    /** ============================
     *  UI Preferences
     *  ============================ */

    /**
     * Fetch the user’s saved theme preference.
     */
    getTheme(): Promise<APIResponse<{ theme: "light" | "dark" | "system" }>> {
        return APIService.apiCall(`${BASE_PATH}/theme`, "GET");
    },

    /**
     * Set a user’s preferred UI theme.
     * @param theme - Theme selection
     */
    setTheme(theme: "light" | "dark" | "system"): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/theme`, "POST", { theme });
    },
};

export default SettingsService;
