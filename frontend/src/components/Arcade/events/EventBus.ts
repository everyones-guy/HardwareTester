
// File: src/components/Arcade/events/EventBus.ts
import mitt from "mitt";

// Central event bus for React <-> Phaser <-> Services
export type ArcadeEvents = {
    "mqtt:send": { topic: string; payload: string };
    "hardware:discover": void;
    "hardware:select": { deviceId: string };
    "firmware:flash": { deviceId: string; firmwareId: string };
    "ui:toast": { message: string };
};

export const ArcadeEventBus = mitt<ArcadeEvents>();