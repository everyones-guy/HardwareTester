// src/types/logTypes.ts

/**
 * Payload for logging an activity
 */
export interface LogActivityPayload {
    user_id: number;
    action: string;
}

/**
 * Optional filters for retrieving activity logs
 */
export interface LogQueryParams {
    user_id?: number;
    start_date?: string;
    end_date?: string;
}

/**
 * Response structure for fetched activity logs
 */
export interface LogEntry {
    timestamp: string;
    action: string;
    user_id: number;
}

/**
 * Payload for sending a notification
 */
export interface NotificationPayload {
    message: string;
    user_id?: number;
}

/**
 * Parameters for querying notifications
 */
export interface NotificationQueryParams {
    user_id?: number;
    only_unread?: boolean;
}

/**
 * Notification entry structure
 */
export interface NotificationEntry {
    id: number;
    message: string;
    is_read: boolean;
    timestamp: string;
    user_id?: number;
}
