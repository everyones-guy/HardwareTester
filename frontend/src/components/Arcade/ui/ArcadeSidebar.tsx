// File: src/components/Arcade/ui/ArcadeSidebar.tsx
import React from "react";
import { useArcadeStore } from "@/components/Arcade/utils/arcadeStore";

export default function ArcadeSidebar() {
    const inventory = useArcadeStore(s => s.inventory);
    const quests = useArcadeStore(s => s.quests);
    const metrics = useArcadeStore(s => s.metrics);


    return (
        <aside className="w-80 border-l p-4 space-y-4">
            <section>
                <h2 className="text-lg font-semibold">Inventory</h2>
                <ul className="list-disc pl-5 text-sm">
                    {inventory.map((it, idx) => (
                        <li key={idx}>{it.name} {it.qty > 1 ? `x${it.qty}` : ""}</li>
                    ))}
                    {inventory.length === 0 && <li>Empty</li>}
                </ul>
            </section>


            <section>
                <h2 className="text-lg font-semibold">Quests</h2>
                <ul className="list-disc pl-5 text-sm">
                    {quests.map(q => (
                        <li key={q.id}>
                            <span className="font-medium">{q.title}</span> — {q.status}
                        </li>
                    ))}
                    {quests.length === 0 && <li>No active quests</li>}
                </ul>
            </section>


            <section>
                <h2 className="text-lg font-semibold">BVT Metrics</h2>
                <div className="text-xs grid grid-cols-2 gap-2">
                    <div>Pass:</div><div>{metrics.pass}</div>
                    <div>Fail:</div><div>{metrics.fail}</div>
                    <div>Running:</div><div>{metrics.running ? "yes" : "no"}</div>
                    <div>Current:</div><div className="col-span-2 truncate">{metrics.current}</div>
                </div>
            </section>
        </aside>
    );
}