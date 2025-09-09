// File: src/components/Arcade/hooks/useArcadeDiscovery.ts
import { useEffect, useRef } from "react";
import HardwareService from "@/services/hardwareService";
import { DevicesUpdatedEvent, DeviceSummary, ArcadeEventBus } from "../events/EventBus";
import { useArcadeStore } from "../utils/arcadeStore";
import type { Device } from "@/types/hardwareTypes";

/**
 * Minimal-change wrapper that:
 *  - handles EventBus requests to discover hardware
 *  - prefers extended discovery (with mock fallback)
 *  - streams live updates if backend supports WS/SSE
 *  - syncs results to the Arcade store
 */
export default function useArcadeDiscovery() {
    const setDevices = useArcadeStore(s => s.setDevices);
    const setMetrics = useArcadeStore(s => s.setMetrics); // optional reuse for discovery status if desired
    const unsubscribeRef = useRef<null | (() => void)>(null);

    useEffect(() => {
        let unsub: (() => void) | null = null;

        async function bootstrap() {
            // Get initial snapshot
            const snapshot = await HardwareService.discoverAll();
            emitFrom(snapshot);
            // Live stream or polling
            unsub = HardwareService.subscribeToDiscovery((list: any[]) => {
                emitFrom(list);
            });
        }

        function emitFrom(list: any[]) {
            // Map your real device objects to DeviceSummary
            const devices = list.map(d => ({
                id: d.id ?? d.device_id ?? String(d.name ?? "device"),
                name: d.name ?? d.model ?? "Device",
                type: normalizeType(d.type ?? d.transport ?? "Other"),
                online: d.status === "online" || d.available === true,
            }));

            const payload: DevicesUpdatedEvent = {
                controllerId: null, // or pick your current controller id if you track one
                devices,
            };
            ArcadeEventBus.emit<DevicesUpdatedEvent>("devices.updated", payload);
        }

        async function doDiscover() {
            // Prefer the extended helper; falls back to mock automatically
            const scan = await (HardwareService as any).discoverDevicesExtended?.() ?? { devices: [] as Device[] };
            setDevices(scan.devices);
        }

        function emitDevicesUpdated(devices: Device[]) {
            const mapped: DeviceSummary[] = devices.map(d => ({
                id: String(d.id ?? d.device_id ?? d.name ?? cryptoRandom()),
                name: String(d.name ?? d.model ?? "Device"),
                type: normalizeType(d.type ?? (d as any).transport ?? "Other"),
                online: d.status === "online" || (d as any).available === true,
            }));

            const payload: DevicesUpdatedEvent = { controllerId: null, devices: mapped };
            ArcadeEventBus.emit("devices:updated", payload);
        }

        function normalizeType(t: string): DeviceSummary["type"] {
            const s = (t || "").toLowerCase();
            if (s.includes("usb")) return "USB";
            if (s.includes("wifi") || s.includes("wi-fi")) return "WiFi";
            if (s.includes("ble") || s.includes("bluetooth")) return "Bluetooth";
            if (s.includes("serial") || s.includes("com")) return "Serial";
            return "Other";
        }
        function cryptoRandom() { return Math.random().toString(36).slice(2); }

        function startStreaming() {
            // Try WS first; if not available, try SSE; otherwise, no-op
            const svc: any = HardwareService as any;
            if (typeof svc.subscribeToDiscoveryWS === "function") {
                unsubscribeRef.current = svc.subscribeToDiscoveryWS((devices: Device[]) => setDevices(devices));
            } else if (typeof svc.subscribeToDiscoverySSE === "function") {
                unsubscribeRef.current = svc.subscribeToDiscoverySSE((devices: Device[]) => setDevices(devices));
            }
        }

        const onDiscover = async () => {
            try {
                setMetrics?.({ current: "Discovering devices...", running: true });
                await doDiscover();
                emitDevicesUpdated(scan.devices);
                startStreaming();
            } finally {
                setMetrics?.({ running: false });
            }
        };

        ArcadeEventBus.on("hardware:discover", onDiscover);
        return () => {
            ArcadeEventBus.off("hardware:discover", onDiscover as any);
            if (unsubscribeRef.current) unsubscribeRef.current();
            unsubscribeRef.current = null;
        };
    }, [setDevices, setMetrics]);
}