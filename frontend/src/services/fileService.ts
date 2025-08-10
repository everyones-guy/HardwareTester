// src/services/fileService.ts
import APIService, { getWebSocketURL } from "@/services/apiService";
import { APIResponse } from "@/types/apiTypes";

const BASE_PATH = "files";

const FileService = {
    /**
     * Download a snapshot file as a Blob.
     * @param filename - Target file name
     */
    async downloadSnapshot(filename: string): Promise<Blob | null> {
        const response = await APIService.apiCall(`${BASE_PATH}/snapshots/${filename}`, "GET", null, {}, "blob");
        return response instanceof Blob ? response : null;
    },

    /**
     * List all available snapshot files.
     */
    listSnapshots(): Promise<APIResponse<{ files: string[] }>> {
        return APIService.apiCall(`${BASE_PATH}/snapshots`, "GET");
    },

    /**
     * Delete a snapshot file.
     * @param filename - Target file name
     */
    deleteSnapshot(filename: string): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/snapshots/${filename}`, "DELETE");
    },

    /**
     * Upload a snapshot or config file.
     * @param file - File to upload
     */
    uploadFile(file: File): Promise<APIResponse> {
        const formData = new FormData();
        formData.append("file", file);
        return APIService.apiCall(`${BASE_PATH}/upload`, "POST", formData, {
            "Content-Type": "multipart/form-data",
        });
    },

    /**
     * Subscribe to file-related backend events (e.g., parse progress, result).
     * @param callback - Function to receive updates
     * @returns Unsubscribe function
     */
    subscribeToFileEvents(callback: (update: any) => void): () => void {
        const socket = new WebSocket(getWebSocketURL(`${BASE_PATH}/events`));

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                callback(data);
            } catch (err) {
                console.error("FileEvent WebSocket parse error:", err);
            }
        };

        socket.onerror = (err) => {
            console.error("FileEvent WebSocket error:", err);
        };

        return () => socket.close();
    },
};

export default FileService;
