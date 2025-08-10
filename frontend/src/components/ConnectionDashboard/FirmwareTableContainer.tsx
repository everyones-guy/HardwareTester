// src/components/FirmwareDashboard/FirmwareTableContainer.tsx
import React, { useEffect, useMemo, useState } from "react";
import FirmwareTable from "./FirmwareTable";
import FirmwareService, { listAsTableEntries, FirmwareTableEntry } from "@/services/firmwareService";

interface Props {
    reloadToken?: number; // bump to force reload (e.g., after upload/delete)
    query?: string;       // optional text filter
}

const FirmwareTableContainer: React.FC<Props> = ({ reloadToken, query = "" }) => {
    const [items, setItems] = useState<FirmwareTableEntry[]>([]);
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string | null>(null);

    const load = async () => {
        setLoading(true);
        setErr(null);
        try {
            const rows = await listAsTableEntries();
            setItems(rows);
        } catch (e: any) {
            setErr(e?.message || "Failed to load firmware.");
            setItems([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { load(); }, []);
    useEffect(() => { if (reloadToken !== undefined) load(); }, [reloadToken]);

    const onDownload = async (id: string) => {
        try {
            const fw = items.find((x) => x.id === id);
            const safeName = (fw?.name || "firmware").replace(/[^\w.-]+/g, "_");
            const safeVer = (fw?.version || "latest").replace(/[^\w.-]+/g, "_");
            await FirmwareService.downloadFirmware(id, `${safeName}-${safeVer}.bin`);
        } catch (e: any) {
            alert(e?.message || "Download failed.");
        }
    };

    const onDelete = async (id: string) => {
        if (!confirm("Delete this firmware? This cannot be undone.")) return;
        try {
            await FirmwareService.deleteFirmware(id);
            await load();
        } catch (e: any) {
            alert(e?.message || "Delete failed.");
        }
    };

    const q = query.trim().toLowerCase();
    const filtered = useMemo(() => {
        if (!q) return items;
        return items.filter((fw) =>
            [fw.name, fw.version, fw.deviceType, fw.uploadDate]
                .filter(Boolean)
                .join(" ")
                .toLowerCase()
                .includes(q)
        );
    }, [items, q]);

    return (
        <div>
            <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
                <button onClick={load} disabled={loading}>
                    {loading ? "Refreshing..." : "Refresh"}
                </button>
                {err && <span style={{ color: "crimson" }}>{err}</span>}
            </div>

            <FirmwareTable firmwareList={filtered} onDownload={onDownload} onDelete={onDelete} />
        </div>
    );
};

export default FirmwareTableContainer;
