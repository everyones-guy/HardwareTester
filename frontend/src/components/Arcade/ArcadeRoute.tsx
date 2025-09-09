import React from "react";
import PhaserGame from "@/components/Arcade/PhaserGame";
import ArcadeSidebar from "@/components/Arcade/ui/ArcadeSidebar";
import useArcadeDiscovery from "@/components/Arcade/hooks/useArcadeDiscovery";

export default function ArcadeRoute() {
    useArcadeDiscovery(); // start discovery + event emission

    const addBot = () => (window as any).Arcade?.addPeripheral?.();
    const set5 = () => (window as any).Arcade?.setPeripheralCount?.(5);
    const clear = () => (window as any).Arcade?.setPeripheralCount?.(0);

    return (
        <div className="p-6 space-y-4">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold">UHT Arcade</h1>
                <a href="/" className="underline">Back to Dashboard</a>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">
                <div className="border rounded-xl shadow p-2">
                    <div className="flex gap-2 mb-2">
                        <button onClick={addBot}>Add Peripheral</button>
                        <button onClick={set5}>Set 5</button>
                        <button onClick={clear}>Clear</button>
                    </div>
                    <PhaserGame />
                </div>
                <ArcadeSidebar />
            </div>

            <div className="text-xs text-gray-500">WASD/Arrows to move. Space adds a bot. E to interact.</div>
        </div>
    );
}
