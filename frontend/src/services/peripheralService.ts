// src/services/peripheralService.ts
import APIService, { getWebSocketURL } from "@/services/apiService";
import { APIResponse } from "@/types/apiTypes";
import {
    Peripheral,
    PeripheralConfig,
    PeripheralUpdate,
} from "@/types/peripheralTypes";

const BASE_PATH = "peripherals";

const PeripheralService = {
    /**
     * Fetch list of all registered peripherals.
     */
    listPeripherals(): Promise<APIResponse<{ peripherals: Peripheral[] }>> {
        return APIService.apiCallWithRetry(`${BASE_PATH}/list`, "GET");
    },

    /**
     * Get a single peripheral by ID.
     * @param peripheralId - The peripheral's unique identifier.
     */
    getPeripheralById(peripheralId: string): Promise<APIResponse<Peripheral>> {
        return APIService.apiCallWithRetry(`${BASE_PATH}/get/${peripheralId}`, "GET");
    },

    /**
     * Add a new peripheral using configuration payload.
     */
    addPeripheral(data: PeripheralConfig): Promise<APIResponse> {
        return APIService.apiCallWithRetry(`${BASE_PATH}/add`, "POST", data);
    },

    /**
     * Update an existing peripheral.
     */
    updatePeripheral(peripheralId: string, data: PeripheralConfig): Promise<APIResponse> {
        return APIService.apiCallWithRetry(`${BASE_PATH}/update/${peripheralId}`, "POST", data);
    },

    /**
     * Delete a peripheral by ID.
     */
    deletePeripheral(peripheralId: string): Promise<APIResponse> {
        return APIService.apiCallWithRetry(`${BASE_PATH}/delete/${peripheralId}`, "DELETE");
    },

    /**
     * Map a peripheral to a target.
     * 
     * @param peripheralId
     * @param targetId
     * @returns
     */
    async mapPeripheral(peripheralId: string, targetId: string): Promise<APIResponse> {
        return APIService.apiCallWithRetry(`${BASE_PATH}/map`, "POST", { peripheralId, targetId });
    },

    /**
     * Trigger a functionality or connection test for a peripheral.
     */
    testPeripheral(peripheralId: string): Promise<APIResponse> {
        return APIService.apiCallWithRetry(`${BASE_PATH}/test/${peripheralId}`, "POST");
    },

    /**
     * Upload a peripheral configuration file (.json, .yaml, etc.)
     */
    uploadPeripheralConfig(file: File): Promise<APIResponse> {
        const formData = new FormData();
        formData.append("config", file);
        return APIService.apiCallWithRetry(`${BASE_PATH}/upload`, "POST", formData, {
            "Content-Type": "multipart/form-data",
        });
    },

    /**
     * Subscribe to real-time peripheral updates via WebSocket.
     * @param callback - Handler for receiving updates
     * @returns unsubscribe function
     */
    subscribeToPeripheralUpdates(
        callback: (data: PeripheralUpdate) => void
    ): () => void {
        const socket = new WebSocket(getWebSocketURL(`${BASE_PATH}/updates`));

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                callback(data);
            } catch (err) {
                console.error("Peripheral WebSocket parse error:", err);
            }
        };

        socket.onerror = (err) => {
            console.error("Peripheral WebSocket connection error:", err);
        };

        return () => socket.close();
    },
};

export default PeripheralService;
