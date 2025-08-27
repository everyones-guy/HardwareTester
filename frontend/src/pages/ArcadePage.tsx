// File: src/pages/ArcadePage.tsx
import React from "react";
import ArcadeRoute from "@/components/Arcade/ArcadeRoute";
import useArcade from "@/components/Arcade/hooks/useArcade";

export default function ArcadePage() {
    useArcade();
    return <ArcadeRoute />;
}