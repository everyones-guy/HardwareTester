// src/types/dashboardTypes.ts

export interface DashboardItem {
    id: number;
    user_id: number;
    title: string;
    description: string;
    type: string;
    created_at?: string;
}

export interface DashboardItemPayload {
    user_id: number;
    title: string;
    description: string;
    type?: string; // default: "custom"
}

export interface DashboardUpdatePayload {
    title?: string;
    description?: string;
}

export interface DashboardMetricSummary {
    total_users: number;
    total_devices: number;
    total_notifications: number;
}

export interface DashboardSystemHealth {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    status: string;
}

export interface DashboardOverviewItem {
    title: string;
    description: string;
}

export interface APIResponse {
    success: boolean;
    message?: string;
    error?: string;
}
