// src/services/serialService.ts
import APIService, { getWebSocketURL } from "@/services/apiService";
import type { SerialDeviceInfo, SerialLogUpdate } from "@/types/serialTypes";

const BASE_PATH = "serial";

const SerialService = {
    /**
     * List all available serial ports.
     */
    listSerialPorts: async (): Promise<SerialDeviceInfo[]> => {
        const response = await APIService.apiCallWithRetry<{ ports: SerialDeviceInfo[] }>(
            `${BASE_PATH}/ports`,
            "GET"
        );
        return response?.ports ?? [];
    },

    /**
     * Connect to a serial port.
     */
    connectSerial: async (
        port: string,
        baudrate: number
    ): Promise<{ success: boolean; message?: string }> => {
        return APIService.apiCall(`${BASE_PATH}/connect`, "POST", { port, baudrate });
    },

    /**
     * Send data over the serial port.
     */
    sendSerialData: async (
        data: string
    ): Promise<{ success: boolean; bytesSent?: number }> => {
        return APIService.apiCall(`${BASE_PATH}/send`, "POST", { data });
    },

    /**
     * Disconnect the serial connection.
     */
    disconnectSerial: async (): Promise<{ success: boolean }> => {
        return APIService.apiCall(`${BASE_PATH}/disconnect`, "POST");
    },

    /**
     * Read buffered serial output.
     */
    readSerialBuffer: async (): Promise<string> => {
        const result = await APIService.apiCall<{ data: string }>(
            `${BASE_PATH}/read`,
            "GET"
        );
        return result?.data ?? "";
    },

    /**
     * Subscribe to real-time serial logs.
     */
    subscribeToSerialLogs: (
        callback: (log: SerialLogUpdate) => void
    ): (() => void) => {
        const socket = new WebSocket(getWebSocketURL(`${BASE_PATH}/logs`));

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                callback(data);
            } catch (err) {
                console.error("Serial WebSocket parse error:", err);
            }
        };

        socket.onerror = (err) => {
            console.error("Serial WebSocket error:", err);
        };

        return () => socket.close();
    },
};

export default SerialService;
