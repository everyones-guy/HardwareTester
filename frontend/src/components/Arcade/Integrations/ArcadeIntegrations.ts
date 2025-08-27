// File: src/components/Arcade/integrations/ArcadeIntegrations.ts
import { ArcadeEventBus } from "../events/EventBus";
// Import your existing services. Adjust paths to match your project.
import mqttService from "@/services/mqttService";
import hardwareService from "@/services/hardwareService";
import firmwareService from "@/services/firmwareService";
import notificationService from "@/services/notificationService";

// Wire Arcade events to real services
export function initArcadeIntegrations() {
    ArcadeEventBus.on("ui:toast", ({ message }) => notificationService.toast(message));

    ArcadeEventBus.on("mqtt:send", ({ topic, payload }) => {
        mqttService.publish(topic, payload);
    });

    ArcadeEventBus.on("hardware:discover", async () => {
        const devices = await hardwareService.discoverDevices();
        notificationService.toast(`${devices.length} device(s) discovered`);
    });

    ArcadeEventBus.on("hardware:select", async ({ deviceId }) => {
        await hardwareService.selectDevice(deviceId);
        notificationService.toast(`Selected ${deviceId}`);
    });

    ArcadeEventBus.on("firmware:flash", async ({ deviceId, firmwareId }) => {
        const ok = await firmwareService.flashFirmware(deviceId, firmwareId);
        notificationService.toast(ok ? `Flashed ${firmwareId}` : `Flash failed`);
    });
}