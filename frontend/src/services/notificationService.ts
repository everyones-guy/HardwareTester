// src/services/notificationService.ts
import APIService from "@/services/apiService";
import { APIResponse } from "@/types/apiTypes";
import {
    NotificationCreatePayload,
    NotificationEntry,
} from "@/types/notificationTypes";

const BASE_PATH = "notifications";

const NotificationService = {
    /**
     * Fetch all notifications for a specific user.
     * @param userId - ID of the user
     */
    fetchNotifications(userId: number): Promise<APIResponse<{ notifications: NotificationEntry[] }>> {
        return APIService.apiCall(`${BASE_PATH}/user/${userId}`, "GET");
    },

    /**
     * Mark a specific notification as read.
     * @param notificationId - ID of the notification
     */
    markAsRead(notificationId: number): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/read/${notificationId}`, "POST");
    },

    /**
     * Create a new notification for a user.
     * @param payload - Notification content
     */
    createNotification(payload: NotificationCreatePayload): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/create`, "POST", payload);
    },

    /**
     * Delete a specific notification.
     * @param notificationId - ID of the notification
     */
    deleteNotification(notificationId: number): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/delete/${notificationId}`, "DELETE");
    },

    /**
     * Clear all notifications for a specific user.
     * @param userId - ID of the user
     */
    clearAllNotifications(userId: number): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/clear/${userId}`, "DELETE");
    },

    /**
     * List all notifications globally (admin use).
     */
    listNotifications(): Promise<APIResponse<{ notifications: NotificationEntry[] }>> {
        return APIService.apiCall(`${BASE_PATH}/all`, "GET");
    },
};

export default NotificationService;
