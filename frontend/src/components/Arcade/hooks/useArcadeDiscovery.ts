// File: src/components/Arcade/hooks/useArcadeDiscovery.ts
import { useEffect, useRef } from "react";
import HardwareService from "@/services/hardwareService";
import { ArcadeEventBus } from "../events/EventBus";
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
        async function doDiscover() {
            // Prefer the extended helper; falls back to mock automatically
            const scan = await (HardwareService as any).discoverDevicesExtended?.() ?? { devices: [] as Device[] };
            setDevices(scan.devices);
        }

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