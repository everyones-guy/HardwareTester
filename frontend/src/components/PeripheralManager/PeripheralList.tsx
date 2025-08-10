// src/components/PeripheralManager/PeripheralList.tsx
import React from "react";
import { Peripheral } from "@/types/peripheralTypes";
import Button from "@/components/common/Button";
import "./PeripheralList.css";

type Props = {
    peripherals: Peripheral[];
    refresh: () => void;
    onMap?: (p: Peripheral) => void;
    onDelete?: (id: string) => void;
};

const PeripheralList: React.FC<Props> = ({ peripherals, refresh, onMap, onDelete }) => {
    if (!peripherals?.length) {
        return (
            <div className="peripheral-list">
                <div style={{ marginBottom: 8 }}>
                    <Button onClick={refresh}>Refresh</Button>
                </div>
                <div>No peripherals found.</div>
            </div>
        );
    }

    return (
        <div className="peripheral-list">
            <div style={{ marginBottom: 8, display: "flex", gap: 8 }}>
                <Button onClick={refresh}>Refresh</Button>
            </div>
            <table className="peripherals-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Address/Port</th>
                        <th>Protocol</th>
                        <th style={{ width: 220 }}>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {peripherals.map((p) => {
                        const addr = p?.config?.address || p?.config?.port || "-";
                        const protocol = p?.config?.protocol || "-";
                        return (
                            <tr key={p.id}>
                                <td>{p.name}</td>
                                <td>{p.type}</td>
                                <td>{p.status ?? "-"}</td>
                                <td><code>{addr}</code></td>
                                <td>{protocol}</td>
                                <td>
                                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                                        {onMap && (
                                            <Button size="sm" onClick={() => onMap(p)}>
                                                Map
                                            </Button>
                                        )}
                                        {onDelete && (
                                            <Button size="sm" variant="danger" onClick={() => onDelete(p.id)}>
                                                Delete
                                            </Button>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};

export default PeripheralList;
