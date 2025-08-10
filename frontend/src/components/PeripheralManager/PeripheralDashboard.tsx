// src/components/PeripheralManager/PeripheralDashboard.tsx
import React, { useEffect, useMemo, useState } from "react";
import "./PeripheralDashboard.css";

import Button from "@/components/common/Button";
import ConfirmDialog from "@/components/common/ConfirmDialog";
import PeripheralList from "./PeripheralList";
import AddPeripheralModal from "./AddPeripheralModal";
import PeripheralMapper from "./PeripheralMapper";

import PeripheralService from "@/services/peripheralService";
import { Peripheral, PeripheralInput } from "@/types/peripheralTypes";

const PeripheralDashboard: React.FC = () => {
    const [peripherals, setPeripherals] = useState<Peripheral[]>([]);
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string | null>(null);

    // UI state
    const [showAddModal, setShowAddModal] = useState(false);
    const [showMapper, setShowMapper] = useState(false);
    const [selected, setSelected] = useState<Peripheral | null>(null);

    // delete confirm
    const [showDelete, setShowDelete] = useState(false);
    const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);

    // filters
    const [query, setQuery] = useState("");
    const [typeFilter, setTypeFilter] = useState<string>("All");
    const [onlyConnected, setOnlyConnected] = useState(false);

    const loadPeripherals = async () => {
        setLoading(true);
        setErr(null);
        try {
            // Expecting service to return { data: { peripherals: Peripheral[] } } or similar
            const res = await PeripheralService.listPeripherals();
            const list: Peripheral[] =
                // @ts-ignore tolerate different envelopes
                res?.data?.peripherals ?? res?.peripherals ?? [];
            setPeripherals(Array.isArray(list) ? list : []);
        } catch (e: any) {
            setErr(e?.message || "Failed to load peripherals.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadPeripherals();
    }, []);

    // derive unique types for filter dropdown
    const typeOptions = useMemo(() => {
        const set = new Set<string>();
        peripherals.forEach((p) => p.type && set.add(p.type));
        return ["All", ...Array.from(set).sort()];
    }, [peripherals]);

    const filtered = useMemo(() => {
        const q = query.trim().toLowerCase();
        return peripherals
            .filter((p) => (typeFilter === "All" ? true : p.type === typeFilter))
            .filter((p) => (onlyConnected ? p.status?.toLowerCase() === "online" : true))
            .filter((p) => {
                if (!q) return true;
                const addr = p?.config?.address || p?.config?.port || "";
                return (
                    p.name.toLowerCase().includes(q) ||
                    p.type.toLowerCase().includes(q) ||
                    addr.toLowerCase().includes(q)
                );
            });
    }, [peripherals, typeFilter, onlyConnected, query]);

    const openAdd = () => setShowAddModal(true);

    const handleAddPeripheral = async (input: Omit<PeripheralInput, "id">) => {
        setErr(null);
        try {
            await PeripheralService.addPeripheral(input);
            setShowAddModal(false);
            await loadPeripherals();
        } catch (e: any) {
            setErr(e?.message || "Failed to add peripheral.");
        }
    };

    const handleRequestDelete = (id: string) => {
        setPendingDeleteId(id);
        setShowDelete(true);
    };

    const handleConfirmDelete = async () => {
        if (!pendingDeleteId) return;
        setErr(null);
        try {
            await PeripheralService.deletePeripheral(pendingDeleteId);
            setShowDelete(false);
            setPendingDeleteId(null);
            await loadPeripherals();
        } catch (e: any) {
            setErr(e?.message || "Failed to delete peripheral.");
        }
    };

    const handleOpenMapper = (p: Peripheral) => {
        setSelected(p);
        setShowMapper(true);
    };

    const handleMap = async (m: { peripheralId: string; targetId: string }) => {
        try {
            // implement mapping call in your service if not there yet
            await PeripheralService.mapPeripheral(m.peripheralId, m.targetId);
            await loadPeripherals();
        } catch (e) {
            console.error("Map failed:", e);
        }
    };

    return (
        <div className="peripheral-dashboard">
            <div className="peripheral-header">
                <h1>Peripheral Manager</h1>
                <div className="controls" style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
                    <input
                        placeholder="Search name, type, address…"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                    <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
                        {typeOptions.map((t) => (
                            <option key={t} value={t}>{t}</option>
                        ))}
                    </select>
                    <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <input
                            type="checkbox"
                            checked={onlyConnected}
                            onChange={(e) => setOnlyConnected(e.target.checked)}
                        />
                        Online only
                    </label>
                    <Button onClick={openAdd}>+ Add Peripheral</Button>
                    <Button variant="secondary" onClick={loadPeripherals}>
                        Refresh
                    </Button>
                </div>
            </div>

            {err && <div className="error" style={{ marginTop: 8 }}>{err}</div>}

            <PeripheralList
                peripherals={filtered}
                refresh={loadPeripherals}
                // optional callbacks if your list supports actions:
                onMap={handleOpenMapper}
                onDelete={handleRequestDelete}
            />

            {showAddModal && (
                <AddPeripheralModal
                    onAdd={handleAddPeripheral}
                    onClose={() => setShowAddModal(false)}
                />
            )}

            {showMapper && selected && (
                <PeripheralMapper
                    peripheral={selected}
                    onMap={handleMap}
                    onClose={() => setShowMapper(false)}
                />
            )}

            <ConfirmDialog
                open={showDelete}
                title="Delete peripheral?"
                message="This action cannot be undone."
                onCancel={() => setShowDelete(false)}
                onConfirm={handleConfirmDelete}
            />
        </div>
    );
};

export default PeripheralDashboard;
