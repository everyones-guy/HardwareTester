import React, { useEffect, useState } from "react";
import "./HostnameManager.css";

const HostnameManager: React.FC = () => {
    const [hostname, setHostname] = useState("");
    const [original, setOriginal] = useState("");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchHostname();
    }, []);

    const fetchHostname = async () => {
        try {
            const res = await fetch("/settings/hostname");
            const data = await res.json();
            setHostname(data.hostname);
            setOriginal(data.hostname);
        } catch (err) {
            console.error("Failed to load hostname:", err);
        }
    };

    const handleSave = async () => {
        try {
            setLoading(true);
            const res = await fetch("/settings/hostname", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ hostname }),
            });
            if (!res.ok) throw new Error("Save failed.");
            setOriginal(hostname);
            alert("Hostname updated successfully.");
        } catch (err) {
            console.error(err);
            alert("Error saving hostname.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="hostname-manager">
            <h3>Hostname</h3>
            <input
                type="text"
                value={hostname}
                onChange={(e) => setHostname(e.target.value)}
            />
            <button
                onClick={handleSave}
                disabled={loading || hostname === original}
            >
                {loading ? "Saving..." : "Save Hostname"}
            </button>
        </div>
    );
};

export default HostnameManager;
