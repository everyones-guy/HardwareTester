import React from "react";
import GlobalSettings from "./GlobalSettings";
import HostnameManager from "./HostnameManager";
import ThemeSwitcher from "./ThemeSwitcher";
import "./SettingsPanel.css";

const SettingsPanel: React.FC = () => {
    return (
        <div className="settings-panel">
            <h1>System Settings</h1>

            <div className="settings-section">
                <GlobalSettings />
            </div>

            <div className="settings-section">
                <HostnameManager />
            </div>

            <div className="settings-section">
                <ThemeSwitcher />
            </div>
        </div>
    );
};

export default SettingsPanel;
