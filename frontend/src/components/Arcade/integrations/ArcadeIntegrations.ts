// File: src/components/Arcade/integrations/ArcadeIntegrations.ts
import { ArcadeEventBus } from "@/components/Arcade/events/EventBus";
import { useArcadeStore } from "@/components/Arcade/utils/arcadeStore"
import mqttService from "@/services/mqttService";
import hardwareService from "@/services/hardwareService";
import firmwareService from "@/services/firmwareService";
import notificationService from "@/services/notificationService";
import testService from "@/services/testService";


export function initArcadeIntegrations() {
    ArcadeEventBus.on("ui:toast", ({ message }) => notificationService.toast(message));


    ArcadeEventBus.on("mqtt:send", ({ topic, payload }) => mqttService.publish(topic, payload));


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


    ArcadeEventBus.on("tests:metrics", ({ passed, failed, duration }) => {
        notificationService.toast(`BVT Results — Passed: ${passed}, Failed: ${failed}, Duration: ${duration}s`);
    });

    // Inventory bridge: allow scenes to push items via events on the game
    // Each scene can: this.events.emit("arcade:addItem", { name: "Peripheral Bot" })
    window.addEventListener("arcade:addItem", (e: any) => {
        useArcadeStore.getState().addItem(e.detail.name, 1);
    });

    // Tests/BVT handlers
    ArcadeEventBus.on("tests:bvt:start", async () => {
        useArcadeStore.getState().setMetrics({ running: true, current: "" });
        try {
            await testService.startBVT();
            // Subscribe to metrics stream
            testService.subscribeToTestMetrics((m) => {
                useArcadeStore.getState().setMetrics({
                    pass: m.pass,
                    fail: m.fail,
                    current: m.currentTestName,
                    running: m.running,
                });
            });
        } catch (err) {
            useArcadeStore.getState().setMetrics({ running: false });
        }
    });
}