// File: src/components/Arcade/events/EventBus.ts
import mitt, { Emitter } from "mitt";

export type DeviceSummary = {
    id: string;
    name: string;
    type: "USB" | "WiFi" | "Bluetooth" | "Serial" | "Other";
    online?: boolean;
};

export type DevicesUpdatedEvent = {
    controllerId?: string | null;
    devices: DeviceSummary[];
};

export type ArcadeEvents = {
    "mqtt:send": { topic: string; payload: string };
    "hardware:discover": void;
    "hardware:select": { deviceId: string };
    "firmware:flash": { deviceId: string; firmwareId: string };
    "ui:toast": { message: string };
    "tests:metrics": { passed: number; failed: number; duration: number };
    "devices:updated": DevicesUpdatedEvent;
};

// Extend the emitter type with our shim
type ArcadeEmitter = Emitter<ArcadeEvents> & { removeAllListeners: () => void };

// Create the bus
export const ArcadeEventBus = mitt<ArcadeEvents>() as ArcadeEmitter;

// Shim: clear all listeners (mitt keeps them in `all`)
ArcadeEventBus.removeAllListeners = () => {
    const anyBus = ArcadeEventBus as unknown as { all?: Map<unknown, Set<Function>> | Record<string, Set<Function>> };
    const all = anyBus.all;
    if (!all) return;

    // mitt v3: `all` is a Map
    if (all instanceof Map) {
        all.clear();
        return;
    }

    // older/other shapes: `all` might be a plain object
    for (const k of Object.keys(all)) {
        // @ts-ignore
        delete all[k];
    }
};
