// src/components/EmulatorDashboard/ActiveEmulations.tsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import EmulatorService from "@/services/emulatorApiService";
import { EmulationSession } from "@/types/emulatorTypes";
import "./ActiveEmulations.css";

const ActiveEmulations: React.FC = () => {
    const [emulations, setEmulations] = useState<EmulationSession[]>([]);
    const [filter, setFilter] = useState<string>("");
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string | null>(null);
    const [autoRefresh, setAutoRefresh] = useState(true);
    const timer = useRef<number | null>(null);

    const fetchEmulations = async () => {
        setLoading(true);
        setErr(null);
        try {
            const res = await EmulatorService.listActiveEmulations();
            const list: EmulationSession[] =
                // tolerate various envelopes: {success,data:{emulations}}, {emulations}, or raw array
                (res as any)?.data?.emulations ??
                (res as any)?.emulations ??
                (Array.isArray(res) ? (res as any) : []);
            setEmulations(Array.isArray(list) ? list : []);
        } catch (e: any) {
            console.error("Error fetching emulations:", e);
            setErr(e?.message || "Failed to load emulations.");
            setEmulations([]);
        } finally {
            setLoading(false);
        }
    };

    // initial + auto refresh
    useEffect(() => {
        fetchEmulations();
    }, []);
    useEffect(() => {
        if (!autoRefresh) {
            if (timer.current) clearInterval(timer.current);
            timer.current = null;
            return;
        }
        timer.current = window.setInterval(fetchEmulations, 10_000);
        return () => {
            if (timer.current) clearInterval(timer.current);
            timer.current = null;
        };
    }, [autoRefresh]);

    // debounce filter
    const [q, setQ] = useState(filter);
    useEffect(() => {
        const id = window.setTimeout(() => setQ(filter.trim().toLowerCase()), 200);
        return () => clearTimeout(id);
    }, [filter]);

    const filtered = useMemo(() => {
        if (!q) return emulations;
        return emulations.filter((em) =>
            Object.values(em)
                .filter((v) => v != null && typeof v !== "object")
                .some((v) => String(v).toLowerCase().includes(q))
        );
    }, [emulations, q]);

    return (
        <div className="active-emulations">
            <div className="emulation-header">
                <h3>Active Emulations</h3>
                <div className="emulation-controls">
                    <input
                        type="text"
                        placeholder="Filter..."
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                    />
                    <button onClick={fetchEmulations} disabled={loading}>
                        {loading ? "Refreshing..." : "Refresh"}
                    </button>
                    <label style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
                        <input
                            type="checkbox"
                            checked={autoRefresh}
                            onChange={() => setAutoRefresh((v) => !v)}
                        />
                        Auto refresh
                    </label>
                </div>
            </div>

            {err && <div className="error" style={{ marginBottom: 8 }}>{err}</div>}

            <div className="emulation-table-wrapper">
                <table className="emulation-table">
                    <thead>
                        <tr>
                            <th>Machine</th>
                            <th>Blueprint</th>
                            <th>Stress Test</th>
                            <th>Start Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filtered.length > 0 ? (
                            filtered.map((em, idx) => (
                                <tr key={`${em.machine_name}-${em.start_time}-${idx}`}>
                                    <td>{em.machine_name}</td>
                                    <td>{em.blueprint}</td>
                                    <td>{em.stress_test ? "Yes" : "No"}</td>
                                    <td>{em.start_time ? new Date(em.start_time).toLocaleString() : "-"}</td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={4} className="empty-state">
                                    {loading ? "Loading…" : "No emulations found."}
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ActiveEmulations;
