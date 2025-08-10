// src/services/blueprintService.ts
import APIService from "@/services/apiService";
import { APIResponse } from "@/types/apiTypes";
import { Blueprint } from "@/types/blueprintTypes";

const BASE_PATH = "blueprints";

const BlueprintService = {
    /**
     * Scan a machine (by IP, URL, or path) to generate a new blueprint.
     * @param machineAddress - IP address, local path, or hostname
     */
    scanMachine(machineAddress: string): Promise<APIResponse<Blueprint>> {
        return APIService.apiCall(`${BASE_PATH}/scan`, "POST", { machineAddress });
    },

    /**
     * List all saved blueprints in the system.
     */
    listBlueprints(): Promise<APIResponse<{ blueprints: Blueprint[] }>> {
        return APIService.apiCall(`${BASE_PATH}/list`, "GET");
    },

    /**
     * Delete a blueprint by ID or name.
     * @param blueprintId - Unique identifier or name of the blueprint
     */
    deleteBlueprint(blueprintId: string): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/delete/${blueprintId}`, "DELETE");
    },
};

export default BlueprintService;
