// src/types/serialTypes.ts

/**
 * Basic information about an available serial device.
 */
export interface SerialDeviceInfo {
    path: string;
    manufacturer?: string;
    serialNumber?: string;
    vendorId?: string;
    productId?: string;
    [key: string]: any;
}

/**
 * Format of a log update coming from the serial WebSocket.
 */
export interface SerialLogUpdate {
    timestamp: string;
    data: string;
    port?: string;
    type?: "info" | "error" | "warning" | string;
}
