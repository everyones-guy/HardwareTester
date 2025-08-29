// File: src/components/Arcade/utils/arcadeStore.ts
import { create } from "zustand";
export type InventoryItem = { name: string; qty: number };
export type Quest = { id: string; title: string; status: "open" | "done" };
export type Metrics = { pass: number; fail: number; running: boolean; current: string };


interface ArcadeState {
    inventory: InventoryItem[];
    quests: Quest[];
    metrics: Metrics;
    devices?: { id: string; name: string }[]; // light-weight for sidebar
    addItem: (name: string, qty?: number) => void;
    setQuests: (qs: Quest[]) => void;
    setMetrics: (m: Partial<Metrics>) => void;
    setDevices: (ds: { id: string; name: string }[]) => void;
}


export const useArcadeStore = create<ArcadeState>((set) => ({
    inventory: [],
    quests: [],
    metrics: { pass: 0, fail: 0, running: false, current: "" },
    devices: [],
    addItem: (name, qty = 1) => set(s => {
        const idx = s.inventory.findIndex(i => i.name === name);
        if (idx >= 0) {
            const copy = [...s.inventory];
            copy[idx] = { ...copy[idx], qty: copy[idx].qty + qty };
            return { inventory: copy };
        }
        return { inventory: [...s.inventory, { name, qty }] };
    }),
    setQuests: (qs) => set({ quests: qs }),
    setMetrics: (m) => set(s => ({ metrics: { ...s.metrics, ...m } })),
    setDevices: (ds) => set({ devices: ds.map(d => ({ id: (d as any).id, name: (d as any).name })) }),
}));