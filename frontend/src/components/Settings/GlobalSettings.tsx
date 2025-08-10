import React, { useEffect, useState } from "react";
import "./GlobalSettings.css";

interface GlobalConfig {
    timezone: string;
    language: string;
    defaultTimeout: number;
}

const GlobalSettings: React.FC = () => {
    const [settings, setSettings] = useState<GlobalConfig>({
        timezone: "UTC",
        language: "en",
        defaultTimeout: 30,
    });

    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        try {
            const res = await fetch("/settings/global");
            const data = await res.json();
            setSettings(data);
        } catch (err) {
            console.error("Failed to load global settings:", err);
        }
    };

    const handleChange = (field: keyof GlobalConfig, value: string | number) => {
        setSettings((prev) => ({ ...prev, [field]: value }));
    };

    const handleSave = async () => {
        try {
            setLoading(true);
            const res = await fetch("/settings/global", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(settings),
            });
            if (!res.ok) throw new Error("Save failed.");
            alert("Global settings saved.");
        } catch (err) {
            console.error(err);
            alert("Error saving settings.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="global-settings">
            <h3>Global Settings</h3>

            <label>Timezone:</label>
            <select
                value={settings.timezone}
                onChange={(e) => handleChange("timezone", e.target.value)}
            >
                <option value="UTC">UTC</option>
                <option value="America/Chicago">America/Chicago</option>
                <option value="Europe/London">Europe/London</option>
                {/* Add more as needed */}
            </select>

            <label>Language:</label>
            <select
                value={settings.language}
                onChange={(e) => handleChange("language", e.target.value)}
            >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="de">German</option>
            </select>

            <label>Default Timeout (seconds):</label>
            <input
                type="number"
                value={settings.defaultTimeout}
                onChange={(e) => handleChange("defaultTimeout", parseInt(e.target.value))}
            />

            <button onClick={handleSave} disabled={loading}>
                {loading ? "Saving..." : "Save Settings"}
            </button>
        </div>
    );
};

export default GlobalSettings;
