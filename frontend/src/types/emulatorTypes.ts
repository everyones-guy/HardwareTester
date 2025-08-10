// src/types/emulatorTypes.ts

export interface EmulationSession {
    machine_name: string;
    blueprint: string;
    stress_test: boolean;
    start_time: string;
}

export interface BlueprintSummary {
    name: string;
    description: string;
    created_at: string;
}

export interface BlueprintDetail extends BlueprintSummary {
    configuration: Record<string, any>;
}

export interface EmulatorLogEntry {
    timestamp: string;
    message: string;
}

export interface BlueprintUploadResult {
    id: number;
    filename: string;
}

export interface PeripheralInput {
    name: string;
    type: string;
    properties: Record<string, any>;
}
