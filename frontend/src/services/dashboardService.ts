// src/services/dashboardService.ts
import APIService from "@/services/apiService";
import { APIResponse } from "@/types/apiTypes";
import {
    DashboardItem,
    DashboardItemPayload,
    DashboardUpdatePayload,
    DashboardMetricSummary,
    DashboardSystemHealth,
    DashboardOverviewItem,
} from "@/types/dashboardTypes";

const BASE_PATH = "dashboard";

const DashboardService = {
    /**
     * Get dashboard data entries for a specific user.
     * @param userId - ID of the target user
     */
    getDashboardData(userId: number): Promise<APIResponse<{ data: DashboardItem[] }>> {
        return APIService.apiCall(`${BASE_PATH}/user/${userId}`, "GET");
    },

    /**
     * Create a new dashboard entry.
     * @param payload - Dashboard item creation data
     */
    createDashboardItem(payload: DashboardItemPayload): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/create`, "POST", payload);
    },

    /**
     * Update an existing dashboard entry by ID.
     * @param itemId - ID of the dashboard item
     * @param data - Updated fields
     */
    updateDashboardItem(itemId: number, data: DashboardUpdatePayload): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/update/${itemId}`, "POST", data);
    },

    /**
     * Delete a dashboard item by ID.
     * @param itemId - ID of the dashboard entry
     */
    deleteDashboardItem(itemId: number): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/delete/${itemId}`, "DELETE");
    },

    /**
     * Get real-time aggregated dashboard metrics (total users, devices, etc.)
     */
    getAggregatedMetrics(): Promise<APIResponse<{ metrics: DashboardMetricSummary }>> {
        return APIService.apiCall(`${BASE_PATH}/metrics`, "GET");
    },

    /**
     * Get system-level health info (CPU, memory, disk usage).
     */
    getSystemHealth(): Promise<APIResponse<{ data: DashboardSystemHealth }>> {
        return APIService.apiCall(`${BASE_PATH}/health`, "GET");
    },

    /**
     * Get user-specific dashboard overview summary.
     * @param userId - ID of the user
     */
    getUserOverview(userId: number): Promise<APIResponse<{ data: DashboardOverviewItem[] }>> {
        return APIService.apiCall(`${BASE_PATH}/overview/${userId}`, "GET");
    },
};

export default DashboardService;
