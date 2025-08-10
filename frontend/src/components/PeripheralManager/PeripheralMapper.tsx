import React, { useEffect, useState } from "react";
import "./PeripheralMapper.css";
import Button from "@/components/common/Button";
import APIService from "@/services/apiService";
import { Peripheral } from "@/types/peripheralTypes";

interface MappingTarget {
    id: string;
    label: string;
}

interface PeripheralMapperProps {
    peripheral: Peripheral;
    onMap: (mapping: { peripheralId: string; targetId: string }) => void;
    onClose: () => void;
}

const PeripheralMapper: React.FC<PeripheralMapperProps> = ({
    peripheral,
    onMap,
    onClose,
}) => {
    const [targets, setTargets] = useState<MappingTarget[]>([]);
    const [selectedTarget, setSelectedTarget] = useState<string>("");
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string | null>(null);

    useEffect(() => {
        loadMappingTargets();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const loadMappingTargets = async () => {
        setLoading(true);
        setErr(null);
        try {
            // assumes backend route GET /api/mapping/targets -> { targets: MappingTarget[] }
            const res = await APIService.apiCallWithRetry<{ targets: MappingTarget[] }>(
                "mapping/targets",
                "GET"
            );
            setTargets(res?.targets ?? []);
        } catch (e: any) {
            console.error("Failed to load mapping targets:", e);
            setErr(e?.message || "Failed to load mapping targets.");
        } finally {
            setLoading(false);
        }
    };

    const handleMap = () => {
        if (!selectedTarget) {
            alert("Select a target to map.");
            return;
        }
        onMap({ peripheralId: peripheral.id, targetId: selectedTarget });
        onClose();
    };

    const addr = peripheral?.config?.address || peripheral?.config?.port || "-";

    return (
        <div className="peripheral-mapper-overlay" onClick={onClose}>
            <div className="peripheral-mapper-modal" onClick={(e) => e.stopPropagation()}>
                <h3>Map Peripheral</h3>

                <div className="peripheral-summary">
                    <p>
                        <strong>{peripheral.name}</strong> ({peripheral.type})
                    </p>
                    <p>
                        Address/Port: <code>{addr}</code>
                    </p>
                </div>

                {err && <div className="error">{err}</div>}

                <label>
                    <span>Target</span>
                    <select
                        value={selectedTarget}
                        onChange={(e) => setSelectedTarget(e.target.value)}
                        disabled={loading || targets.length === 0}
                    >
                        <option value="">-- Select Target --</option>
                        {targets.map((t) => (
                            <option key={t.id} value={t.id}>
                                {t.label}
                            </option>
                        ))}
                    </select>
                </label>

                <div className="modal-actions">
                    <Button onClick={handleMap} disabled={!selectedTarget || loading}>
                        Map
                    </Button>
                    <Button variant="secondary" onClick={onClose}>
                        Cancel
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default PeripheralMapper;
