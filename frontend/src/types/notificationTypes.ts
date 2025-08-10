// src/types/notificationTypes.ts

/**
 * Notification record returned by the backend.
 */
export interface NotificationEntry {
    id: number;
    message: string;
    type: string;
    read: boolean;
    timestamp: string;
    user_id?: number;
}

/**
 * Payload to create a new notification.
 */
export interface NotificationCreatePayload {
    user_id: number;
    message: string;
    notification_type?: string; // "info" | "warning" | "error"
}
