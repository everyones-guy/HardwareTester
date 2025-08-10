// src/types/configurationTypes.ts

export interface ConfigurationLayout {
    [key: string]: any; // Could represent UI widget layout or device map
}

export interface DynamicConfigData {
    type: string;
    name?: string;
    description?: string;
    properties: Record<string, any>;
}

export interface ConfigurationResult {
    success: boolean;
    message?: string;
    error?: string;
}

export interface DynamicConfigResult {
    success: boolean;
    message?: string;
    error?: string;
}

export interface LoadedConfig {
    success: boolean;
    configuration?: {
        name: string;
        layout: ConfigurationLayout;
    };
    error?: string;
}

export interface PaginatedConfigs {
    success: boolean;
    configurations: { id: string; name: string }[];
    total: number;
    error?: string;
}
