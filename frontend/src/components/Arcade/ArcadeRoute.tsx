// File: src/components/Arcade/ArcadeRoute.tsx
import React from "react";
import { Link } from "react-router-dom";
import PhaserGame from "./PhaserGame";

/**
 * Route wrapper for the Arcade view.
 * - Uses <a> for nav (user preference) and reserves <button> for actions
 */
export default function ArcadeRoute() {
    return (
        <div className="p-6 space-y-4">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold">UHT Arcade</h1>
                <a href="/" className="underline">Back to Dashboard</a>
            </div>
            <p className="text-sm max-w-3xl">
                Walk your bot through rooms to assemble controllers, connect peripherals, flash firmware, and run tests.
                The game talks to the existing services (MQTT, hardware, firmware) via an event bus.
            </p>
            <div className="border rounded-xl shadow p-2">
                <PhaserGame />
            </div>
            <div className="text-xs text-gray-500">
                Tip: WASD/Arrows to move. E to interact. M to toggle minimap.
            </div>
        </div>
    );
}

