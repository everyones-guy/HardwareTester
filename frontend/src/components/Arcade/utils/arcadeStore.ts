// File: src/components/Arcade/utils/arcadeStore.ts
import { create } from "zustand";
export type InventoryItem = { name: string; qty: number };
export type Quest = { id: string; title: string; status: "open" | "done" };
export type Metrics = { pass: number; fail: number; running: boolean; current: string };


interface ArcadeState {
inventory: InventoryItem[];
quests: Quest[];
metrics: Metrics;
addItem: (name: string, qty?: number) => void;
setQuests: (qs: Quest[]) => void;
setMetrics: (m: Partial<Metrics>) => void;
}


export const useArcadeStore = create<ArcadeState>((set) => ({
inventory: [],
quests: [],
metrics: { pass: 0, fail: 0, running: false, current: "" },
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
}));