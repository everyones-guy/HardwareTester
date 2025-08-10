// src/types/peripheralTypes.ts

export interface Peripheral {
    id: string;
    name: string;
    type: string;
    status?: string;
    description?: string;
    config: PeripheralConfig;
}

export interface PeripheralConfig {
    port?: string;
    address?: string;
    baudRate?: number;
    protocol?: "I2C" | "SPI" | "UART" | "CAN" | "GPIO" | string;
    [key: string]: any;
}

export interface PeripheralStatus {
    id: string;
    isConnected: boolean;
    lastChecked: string;
    error?: string;
}
export interface PeripheralUpdate {
    peripheralId: string;
    status: "online" | "offline" | "error" | "warning";
    lastSeen: string; // ISO timestamp
    message?: string;
    [key: string]: any; // Optional for backend flexibility
}

/**
 * Basic peripheral input structure used when adding or updating.
 */
export interface PeripheralInput {
    id?: number;
    name: string;
    type: string;
    port?: string;
    controller_id?: number;
    config?: Record<string, any>; // For dynamic options like baudrate, pins, etc.
    properties?: Record<string, any>; // allow incoming data from backend or legacy code
}