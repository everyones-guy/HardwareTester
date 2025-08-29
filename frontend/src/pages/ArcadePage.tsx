// File: src/pages/ArcadePage.tsx
import React from "react";
import ArcadeRoute from "@/components/Arcade/ArcadeRoute";
import useArcade from "@/components/Arcade/hooks/useArcade";
import useArcadeDiscovery from "@/components/Arcade/hooks/useArcadeDiscovery";


export default function ArcadePage() {
    useArcade();
    useArcadeDiscovery();
    return <ArcadeRoute />;
}