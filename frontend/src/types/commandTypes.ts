// src/types/commandTypes.ts
export interface FirmwareCommand {
    name: string;
    description: string;
    parameters?: Record<string, any>;
}
