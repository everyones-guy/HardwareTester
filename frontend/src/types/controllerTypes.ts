// src/types/controllerTypes.ts

export type ControllerState = "open" | "closed" | "faulty" | "maintenance";

export interface Controller {
    id: string;
    name: string;
    type: string;
    specifications: string;
    state: ControllerState;
}

export interface ControllerAddPayload {
    name: string;
    type: string;
    specifications: string;
    state?: ControllerState;
}

export interface ControllerUpdatePayload {
    name?: string;
    type?: string;
    specifications?: string;
    state?: ControllerState;
}

export interface ControllerOperationResponse {
    success: boolean;
    message?: string;
    error?: string;
}

export interface ControllerStatusResponse {
    success: boolean;
    status?: { id: string; status: ControllerState };
    error?: string;
}

export interface ControllerListResponse {
    success: boolean;
    controllers: Controller[];
    error?: string;
}
