// File: src/components/Arcade/sidepanel/QuestPanel.tsx
import React, { useEffect, useState } from "react";
import { ArcadeEventBus } from "../events/EventBus";

interface QuestLogEntry {
    message: string;
    timestamp: number;
}

export default function QuestPanel() {
    const [log, setLog] = useState<QuestLogEntry[]>([]);

    useEffect(() => {
        function addEntry(msg: string) {
            setLog(prev => [...prev, { message: msg, timestamp: Date.now() }]);
        }

        ArcadeEventBus.on("ui:toast", ({ message }) => addEntry(message));
        ArcadeEventBus.on("tests:metrics", ({ passed, failed }) => addEntry(`BVT Finished: ${passed} passed / ${failed} failed`));

        return () => {
            ArcadeEventBus.all.clear();
        };
    }, []);

    return (
        <div className="border-l p-2 w-64 bg-gray-900 text-gray-200 overflow-y-auto text-sm">
            <h2 className="font-bold text-lg mb-2">Quest Log</h2>
            <ul className="space-y-1">
                {log.map((entry, idx) => (
                    <li key={idx} className="border-b border-gray-700 pb-1">
                        <span className="block">{entry.message}</span>
                        <span className="text-xs text-gray-500">{new Date(entry.timestamp).toLocaleTimeString()}</span>
                    </li>
                ))}
            </ul>
        </div>
    );
}