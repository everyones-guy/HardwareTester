// src/types/mainTypes.ts

/**
 * One dashboard entry for a user’s main panel.
 */
export interface DashboardEntry {
    title: string;
    description: string;
    created_at: string; // ISO datetime string
}

/**
 * Payload structure for saving a contact message.
 */
export interface ContactMessagePayload {
    name: string;
    email: string;
    message: string;
}

/**
 * Payload structure to request server logs.
 */
export interface ErrorLogPayload {
    log_file: string;
}
