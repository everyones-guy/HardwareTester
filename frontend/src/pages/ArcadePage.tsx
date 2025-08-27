// File: src/pages/ArcadePage.tsx
import React from "react";
import ArcadeRoute from "@/components/Arcade/ArcadeRoute";
import useArcade from "@/components/Arcade/hooks/useArcade";
import QuestPanel from "@/components/Arcade/sidepanel/QuestPanel";


export default function ArcadePage() {
    useArcade();
    return (
        <div className="flex">
            <div className="flex-grow">
                <ArcadeRoute />
            </div>
            <QuestPanel />
        </div>
    );
}