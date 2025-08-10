// src/services/configurationService.ts
import APIService from "@/services/apiService";
import { APIResponse } from "@/types/apiTypes";
import {
    ConfigurationLayout,
    DynamicConfigData,
    ConfigurationResult,
    DynamicConfigResult,
    LoadedConfig,
    PaginatedConfigs,
} from "@/types/configurationTypes";

const BASE_PATH = "configurations";

const ConfigurationService = {
    /**
     * Save a new static configuration layout.
     * @param name - Configuration name
     * @param layout - JSON-compatible layout structure
     */
    saveConfiguration(name: string, layout: ConfigurationLayout): Promise<APIResponse<ConfigurationResult>> {
        return APIService.apiCall(`${BASE_PATH}/save`, "POST", { name, layout });
    },

    /**
     * Add a dynamic configuration to the system.
     * @param data - Dynamic configuration data
     * @param userId - ID of the user submitting it
     */
    addDynamicConfiguration(data: DynamicConfigData, userId: string): Promise<APIResponse<DynamicConfigResult>> {
        return APIService.apiCall(`${BASE_PATH}/dynamic`, "POST", { ...data, userId });
    },

    /**
     * Get a paginated list of saved configurations.
     * @param search - Optional search term
     * @param page - Current page number
     * @param perPage - Number of configs per page
     */
    listConfigurations(
        search: string = "",
        page: number = 1,
        perPage: number = 10
    ): Promise<APIResponse<PaginatedConfigs>> {
        const query = new URLSearchParams({
            search,
            page: String(page),
            per_page: String(perPage),
        });
        return APIService.apiCall(`${BASE_PATH}/list?${query}`, "GET");
    },

    /**
     * Load a configuration by its ID.
     * @param configId - Configuration UUID or numeric ID
     */
    loadConfiguration(configId: string): Promise<APIResponse<LoadedConfig>> {
        return APIService.apiCall(`${BASE_PATH}/load/${configId}`, "GET");
    },

    /**
     * Load a configuration by name.
     * @param name - Configuration name
     */
    getConfigurationByName(name: string): Promise<APIResponse<LoadedConfig>> {
        return APIService.apiCall(`${BASE_PATH}/get-by-name/${name}`, "GET");
    },
};

export default ConfigurationService;
