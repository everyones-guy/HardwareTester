// src/services/mainService.ts
import APIService from "@/services/apiService";
import { APIResponse } from "@/types/apiTypes";
import {
    ContactMessagePayload,
    DashboardEntry,
    ErrorLogPayload,
} from "@/types/mainTypes";

const BASE_PATH = "main";

const MainService = {
    /**
     * Fetch dashboard data entries for a specific user.
     * @param userId - ID of the user
     */
    fetchMainDashboardData(userId: number): Promise<APIResponse<{ data: DashboardEntry[] }>> {
        return APIService.apiCall(`${BASE_PATH}/dashboard/${userId}`, "GET");
    },

    /**
     * Submit a contact message.
     * @param payload - Object containing name, email, and message
     */
    saveContactMessage(payload: ContactMessagePayload): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/contact`, "POST", payload);
    },

    /**
     * Fetch server-side error logs from a file.
     * @param payload - Log file to read (default is 'logs/app_error.log')
     */
    fetchErrorLogs(payload: ErrorLogPayload): Promise<APIResponse<{ logs: string[] }>> {
        return APIService.apiCall(`${BASE_PATH}/logs`, "POST", payload);
    },
};

export default MainService;
