// src/services/logService.ts
import APIService from "@/services/apiService";
import { APIResponse } from "@/types/apiTypes";

const BASE_PATH = "logs";

const LogService = {
    /**
     * Log a user activity into the backend.
     * @param userId - ID of the user performing the action
     * @param action - Description of the activity
     */
    logActivity(userId: number, action: string): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/activity`, "POST", {
            user_id: userId,
            action,
        });
    },

    /**
     * Retrieve activity logs with optional filters.
     * @param userId - Optional user ID to filter logs
     * @param startDate - Optional ISO start date
     * @param endDate - Optional ISO end date
     */
    getActivityLogs(
        userId?: number,
        startDate?: string,
        endDate?: string
    ): Promise<APIResponse<{ logs: string[] }>> {
        const params: Record<string, any> = {};
        if (userId !== undefined) params.user_id = userId;
        if (startDate) params.start_date = startDate;
        if (endDate) params.end_date = endDate;

        return APIService.apiCall(`${BASE_PATH}/activity`, "GET", null, params);
    },

    /**
     * Send a notification to one user or all users.
     * @param message - Message to send
     * @param userId - Optional user ID to target a specific user
     */
    sendNotification(message: string, userId?: number): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/notify`, "POST", {
            message,
            user_id: userId,
        });
    },

    /**
     * Fetch notifications for a user or all users.
     * @param userId - Optional user ID to filter by recipient
     * @param onlyUnread - Whether to fetch only unread notifications
     */
    getNotifications(
        userId?: number,
        onlyUnread: boolean = false
    ): Promise<APIResponse<{ notifications: any[] }>> {
        const params: Record<string, any> = {};
        if (userId !== undefined) params.user_id = userId;
        if (onlyUnread) params.only_unread = true;

        return APIService.apiCall(`${BASE_PATH}/notifications`, "GET", null, params);
    },

    /**
     * Mark a notification as read.
     * @param notificationId - ID of the notification to mark
     */
    markNotificationAsRead(notificationId: number): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/notifications/read/${notificationId}`, "POST");
    },
};

export default LogService;
