// File: src/components/Arcade/ArcadeRoute.tsx
import React from "react";
import { Link } from "react-router-dom";
import PhaserGame from "@/components/Arcade/PhaserGame";
import ArcadeSidebar from "@/components/Arcade/ui/ArcadeSidebar";

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
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">
                <div className="border rounded-xl shadow p-2">
                    <PhaserGame />
                </div>
                <ArcadeSidebar />
            </div>
            <div className="text-xs text-gray-500">WASD/Arrows to move. E to interact.</div>
        </div>
    );
}

