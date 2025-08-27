// File: src/components/Arcade/events/EventBus.ts
import mitt from "mitt";


export type ArcadeEvents = {
    "mqtt:send": { topic: string; payload: string };
    "hardware:discover": void;
    "hardware:select": { deviceId: string };
    "firmware:flash": { deviceId: string; firmwareId: string };
    "ui:toast": { message: string };
    "tests:metrics": { passed: number; failed: number; duration: number };
};


export const ArcadeEventBus = mitt<ArcadeEvents>();