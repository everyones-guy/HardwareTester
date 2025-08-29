// src/services/apiService.ts
import axiosInstance from "@/services/axiosInstance";
import { AxiosRequestConfig, AxiosError } from "axios";
import { toast } from "react-toastify";
import { APIState, ErrorEntry, APIResponse } from "@/types/apiTypes";

let apiState: APIState = {
    initialized: false,
    running: false,
    config: {
        default_machine_name: "Session1",
        stress_test_mode: false,
        base_url: null,
        timeout: 10,
    },
    blueprints: [],
    active_sessions: [],
    endpoints: [],
    logs: [],
    errors: [],
    last_updated: null,
};

const logError = (message: string) => {
    const timestamp = new Date().toISOString();
    apiState.errors.push({ timestamp, message });
    apiState.last_updated = timestamp;
    console.error(`[API ERROR] ${message}`);
};

const APIService = {
    /**
     * Initialize the API client.
     */
    initialize(baseUrl: string, timeout: number = 10) {
        if (!baseUrl) throw new Error("Base URL must be provided");
        apiState.config.base_url = baseUrl;
        apiState.config.timeout = timeout;
        apiState.initialized = true;
        apiState.last_updated = new Date().toISOString();
        apiState.logs.push(`Initialized at ${apiState.last_updated}`);
        console.log(`[API INIT] ${baseUrl}`);
    },

    /**
     * Test connection to the backend API.
     */
    async testConnection(): Promise<APIResponse<string>> {
        try {
            await axiosInstance.get("/test-connection");
            return { success: true, data: "API connection successful" };
        } catch (err: any) {
            logError(`API connection failed: ${err.message}`);
            return { success: false, error: `API connection failed: ${err.message}` };
        }
    },

    /**
     * Basic GET with optional query params.
     */
    async fetch<T>(endpoint: string, params?: Record<string, any>): Promise<APIResponse<T>> {
        try {
            const res = await axiosInstance.get<T>(endpoint, { params });
            return { success: true, data: res.data };
        } catch (err: any) {
            logError(`Failed to fetch ${endpoint}: ${err.message}`);
            return { success: false, error: err.message };
        }
    },

    /**
     * Push data to the backend via POST.
     */
    async push(endpoint: string, payload: any): Promise<APIResponse<string>> {
        try {
            await axiosInstance.post(endpoint, payload);
            return { success: true, data: "Data successfully pushed" };
        } catch (err: any) {
            logError(`Failed to push to ${endpoint}: ${err.message}`);
            return { success: false, error: err.message };
        }
    },

    /**
     * List available backend endpoints.
     */
    async listEndpoints(): Promise<APIResponse<string[]>> {
        try {
            const res = await axiosInstance.get("/endpoints");
            const endpoints = res.data?.endpoints || [];
            apiState.endpoints = endpoints;
            apiState.last_updated = new Date().toISOString();
            return { success: true, data: endpoints };
        } catch (err: any) {
            logError(`Failed to list endpoints: ${err.message}`);
            return { success: false, error: err.message };
        }
    },

    /**
     * Get backend summary information.
     */
    async getOverview(): Promise<APIResponse<any>> {
        try {
            const res = await axiosInstance.get("/overview");
            return { success: true, data: res.data };
        } catch (err: any) {
            logError(`Failed to fetch overview: ${err.message}`);
            return { success: false, error: err.message };
        }
    },

    /**
     * Low-level API call wrapper.
     */
    async apiCall<T>(
        url: string,
        method: "GET" | "POST" | "PUT" | "DELETE",
        data: any = null,
        headers: Record<string, string> = {},
        responseType: AxiosRequestConfig["responseType"] = "json",
        timeoutMs?: number
    ): Promise<T> {
        try {
            const config: AxiosRequestConfig = {
                method,
                url,
                data,
                headers,
                responseType,
                timeout: timeoutMs,
            };
            const response = await axiosInstance(config);
            return response.data;
        } catch (error: any) {
            const message = (error as AxiosError)?.message || "API call failed";
            toast.error(`API Error: ${message}`);
            throw error;
        }
    },

    async sleep(ms: number) {
        return new Promise((r) => setTimeout(r, ms));
    },

    /**
     * Compute exponential backoff with full jitter.
     * attempt: 1-based attempt number
     */
    backoffWithJitter(
        baseDelayMs: number,
        attempt: number,
        backoffFactor: number,
        maxDelayMs: number
    ): number {
        const exp = Math.min(maxDelayMs, baseDelayMs * Math.pow(backoffFactor, attempt - 1));
        return Math.floor(Math.random() * exp); // full jitter
    },

    /**
     * Retry-enabled version of apiCall with exponential backoff + Jitter.
     */

    async apiCallWithRetry<T>(
        url: string,
        method: "GET" | "POST" | "PUT" | "DELETE",
        data: any = null,
        headers: Record<string, string> = {},
        retries = 3,
        baseDelayMs = 750,
        backoffFactor = 2,
        maxDelayMs = 10_000,
        baseTimeoutMs?: number,
        maxTimeoutMs = 30_000
    ): Promise<T> {
        const initialTimeoutMs =
            baseTimeoutMs ?? (apiState.config.timeout ? apiState.config.timeout * 1000 : 5_000);

        for (let attempt = 1; attempt <= retries; attempt++) {
            // grow timeout per attempt (capped)
            const attemptTimeoutBase = Math.min(
                maxTimeoutMs,
                initialTimeoutMs * Math.pow(backoffFactor, attempt - 1)
            );
            const attemptTimeoutMs =
                Math.floor(Math.random() * attemptTimeoutBase) || attemptTimeoutBase;

            try {
                // PASS the timeout down to apiCall
                return await APIService.apiCall<T>(
                    url,
                    method,
                    data,
                    headers,
                    "json",
                    attemptTimeoutMs
                );
            } catch (err) {
                if (attempt === retries) throw err;

                // Exponential delay with full jitter before next attempt
                const delay = APIService.backoffWithJitter(baseDelayMs, attempt, backoffFactor, maxDelayMs);
                await APIService.sleep(delay);  // <— FIX: call on APIService
            }
        }
        throw new Error("Unreachable");
    },
    /**
     * Generate the full WebSocket URL based on the configured API base URL.
     * Automatically switches to ws:// or wss:// depending on protocol.
     * @param path - Path to append after /ws/
     */

    getWebSocketURL(path: string): string {
        const baseUrl = apiState.config.base_url || window.location.origin;
        const url = new URL(baseUrl);
        const protocol = url.protocol === "https:" ? "wss:" : "ws:";
        const host = url.host;
        return `${protocol}//${host}/ws/${path}`;
    },
};

export default APIService;
