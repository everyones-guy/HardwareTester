// /src/services/axiosInstance.ts
import axios, {
    AxiosError,
    AxiosRequestConfig,
    AxiosInstance
} from "axios";
import { toast } from "react-toastify";
import {
    getToken,
    setToken,
    clearToken,
} from "@/utils/tokenUtils";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:5000/api"; // || "http://localhost:5000";

const instance: AxiosInstance = axios.create({
    baseURL: API_BASE,
    headers: { "Content-Type": "application/json" },
    withCredentials: false,
});

let isRefreshing = false;

interface RetryRequestConfig extends AxiosRequestConfig {
    _retry?: boolean;
}

interface RefreshResponse {
    token: string;
}

let failedQueue: {
    resolve: (value?: unknown) => void;
    reject: (reason?: any) => void;
    config: AxiosRequestConfig;
}[] = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
    failedQueue.forEach(({ resolve, reject, config }) => {
        if (error) {
            reject(error);
        } else if (token && config.headers) {
            config.headers["Authorization"] = `Bearer ${token}`;
            resolve(instance(config));
        }
    });
    failedQueue = [];
};

// Inject token into requests
instance.interceptors.request.use((config) => {
    const token = getToken();
    if (token && config.headers) {
        config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
});

// Refresh token logic on 401 errors
instance.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const originalRequest = error.config as RetryRequestConfig;

        if (error.response?.status === 401 && !originalRequest._retry) {
            if (isRefreshing) {
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject, config: originalRequest });
                });
            }

            originalRequest._retry = true;
            isRefreshing = true;

            try {
                const response = await axios.post<RefreshResponse>(`${API_BASE}/auth/refresh-token`);
                const newToken = response.data.token;

                setToken(newToken);
                processQueue(null, newToken);

                originalRequest.headers = {
                    ...originalRequest.headers,
                    Authorization: `Bearer ${newToken}`,
                };

                return instance(originalRequest);
            } catch (refreshError) {
                processQueue(refreshError as AxiosError, null);
                clearToken();
                toast.error("Session expired. Please log in again.");
                return Promise.reject(refreshError);
            } finally {
                isRefreshing = false;
            }
        }

        return Promise.reject(error);
    }
);

export default instance;
export type { AxiosError, AxiosRequestConfig };
