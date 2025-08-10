// src/services/controllerService.ts
import APIService from "@/services/apiService";
import { APIResponse } from "@/types/apiTypes";
import {
    Controller,
    ControllerAddPayload,
    ControllerUpdatePayload,
    ControllerStatusResponse,
    ControllerOperationResponse,
    ControllerListResponse,
    ControllerState,
} from "@/types/controllerTypes";

const BASE_PATH = "controllers";

const ControllerService = {
    /**
     * Get list of all registered controllers.
     */
    listControllers(): Promise<APIResponse<ControllerListResponse>> {
        return APIService.apiCall(`${BASE_PATH}/list`, "GET");
    },

    /**
     * Add a new controller.
     * @param data - Controller creation config
     */
    addController(data: ControllerAddPayload): Promise<APIResponse<ControllerOperationResponse>> {
        return APIService.apiCall(`${BASE_PATH}/add`, "POST", data);
    },

    /**
     * Delete a controller by ID.
     * @param controllerId - Unique controller ID
     */
    deleteController(controllerId: string): Promise<APIResponse<ControllerOperationResponse>> {
        return APIService.apiCall(`${BASE_PATH}/delete/${controllerId}`, "DELETE");
    },

    /**
     * Update an existing controller's properties.
     * @param controllerId - Target controller ID
     * @param data - Updated fields
     */
    updateController(
        controllerId: string,
        data: ControllerUpdatePayload
    ): Promise<APIResponse<ControllerOperationResponse>> {
        return APIService.apiCall(`${BASE_PATH}/update/${controllerId}`, "POST", data);
    },

    /**
     * Get the current status of a controller.
     * @param controllerId - Target controller ID
     */
    getControllerStatus(controllerId: string): Promise<APIResponse<ControllerStatusResponse>> {
        return APIService.apiCall(`${BASE_PATH}/status/${controllerId}`, "GET");
    },

    /**
     * Change a controller's operational state.
     * @param controllerId - Target controller ID
     * @param newState - Desired state: open | closed | faulty | maintenance
     */
    changeControllerState(
        controllerId: string,
        newState: ControllerState
    ): Promise<APIResponse<ControllerOperationResponse>> {
        return APIService.apiCall(`${BASE_PATH}/state/${controllerId}`, "POST", { newState });
    },
};

export default ControllerService;
