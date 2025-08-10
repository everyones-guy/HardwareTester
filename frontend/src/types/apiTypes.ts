// src/types/apiTypes.ts

export interface ErrorEntry {
    timestamp: string;
    message: string;
}

export interface APIState {
    initialized: boolean;
    running: boolean;
    config: {
        default_machine_name: string;
        stress_test_mode: boolean;
        base_url: string | null;
        timeout: number;
    };
    blueprints: string[];
    active_sessions: string[];
    endpoints: string[];
    logs: string[];
    errors: ErrorEntry[];
    last_updated: string | null;
}

export interface APIResponse<T = any> {
    success: boolean;
    data?: T;
    message?: string;
    error?: string;
}
