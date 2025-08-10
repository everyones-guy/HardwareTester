// src/types/blueprintTypes.ts

export interface BlueprintDevice {
    type: string;
    os?: string;
    cpu?: string;
    architecture?: string;
    ip?: string;
    reachable?: boolean;
}

export interface Blueprint {
    name: string;
    description: string;
    devices: BlueprintDevice[];
    id?: string;
    created_at?: string;
}
