// src/services/emulatorService.ts
import APIService from "@/services/apiService";
import { APIResponse } from "@/types/apiTypes";
import {
    EmulationSession,
    EmulatorLogEntry,
    BlueprintSummary,
    BlueprintDetail,
    BlueprintUploadResult,
} from "@/types/emulatorTypes";
import { PeripheralInput } from "@/types/peripheralTypes";

const BASE_PATH = "emulators";

const EmulatorService = {
    /**
     * Initialize emulator session state.
     */
    initializeState(): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/initialize`, "POST");
    },

    /**
     * Start a new emulation session.
     */
    startEmulation(
        machine_name: string,
        blueprint_name: string,
        stress_test: boolean = false
    ): Promise<APIResponse<{ message?: string }>> {
        return APIService.apiCall(`${BASE_PATH}/start`, "POST", {
            machine_name,
            blueprint_name,
            stress_test,
        });
    },

    /**
     * Stop an active emulation session.
     */
    stopEmulation(machine_name: string): Promise<APIResponse<{ message?: string }>> {
        return APIService.apiCall(`${BASE_PATH}/stop`, "POST", { machine_name });
    },

    /**
     * List all active emulations.
     */
    listActiveEmulations(): Promise<APIResponse<{ emulations: EmulationSession[] }>> {
        return APIService.apiCall(`${BASE_PATH}/list`, "GET");
    },

    /**
     * Retrieve emulator logs.
     */
    getLogs(): Promise<APIResponse<{ logs: EmulatorLogEntry[] }>> {
        return APIService.apiCall(`${BASE_PATH}/logs`, "GET");
    },

    /**
     * Get all available blueprints.
     */
    fetchBlueprints(): Promise<APIResponse<{ blueprints: BlueprintSummary[] }>> {
        return APIService.apiCall(`${BASE_PATH}/blueprints`, "GET");
    },

    /**
     * Load a blueprint by name.
     */
    loadBlueprint(name: string): Promise<APIResponse<{ blueprint: BlueprintDetail }>> {
        return APIService.apiCall(`${BASE_PATH}/blueprint/${name}`, "GET");
    },

    /**
     * Add a new blueprint manually.
     */
    addBlueprint(
        name: string,
        description: string,
        configuration: Record<string, any>
    ): Promise<APIResponse<{ message: string }>> {
        return APIService.apiCall(`${BASE_PATH}/blueprint/add`, "POST", {
            name,
            description,
            configuration,
        });
    },

    /**
     * Upload a blueprint file (YAML/JSON/etc.).
     */
    uploadBlueprintFile(formData: FormData): Promise<APIResponse<BlueprintUploadResult>> {
        return APIService.apiCall(`${BASE_PATH}/upload`, "POST", formData, {
            "Content-Type": "multipart/form-data",
        });
    },

    /**
     * Load a blueprint from file path.
     */
    loadBlueprintFromFile(path: string): Promise<APIResponse<{ message: string }>> {
        return APIService.apiCall(`${BASE_PATH}/blueprint/load-file`, "POST", { path });
    },

    /**
     * Fetch firmware command definitions for a given blueprint.
     */
    fetchFirmwareCommands(blueprint_name: string): Promise<APIResponse<{ commands: any[] }>> {
        return APIService.apiCall(`${BASE_PATH}/commands/firmware/${blueprint_name}`, "GET");
    },

    /**
     * Fetch dynamic MQTT command definitions from backend.
     */
    fetchMQTTCommands(topic: string): Promise<APIResponse<{ commands: any[] }>> {
        return APIService.apiCall(`${BASE_PATH}/commands/mqtt`, "POST", { topic });
    },

    /**
     * Add or update controller peripherals in bulk.
     */
    addOrUpdatePeripherals(
        controller_id: number,
        peripherals: PeripheralInput[]
    ): Promise<APIResponse<{ message?: string }>> {
        // Map UI -> API wire format
        const payload = peripherals.map(p => ({
            ...p,
            properties: p.config ?? p.properties ?? {},
            config: undefined, // optional: strip UI-only key before sending
        }));

        return APIService.apiCall(
            `${BASE_PATH}/controller/${controller_id}/peripherals`,
            "POST",
            { peripherals: payload }
        );
    },

    /**
     * Enable UI Mirror mode for a given device.
     */
    enableUIMirror(device_id: string): Promise<APIResponse<{ message?: string }>> {
        return APIService.apiCall(`${BASE_PATH}/ui-mirror`, "POST", { device_id });
    },
};

export default EmulatorService;
