// src/components/User/SessionMonitor.tsx
import React from "react";

const SessionMonitor: React.FC = () => {
    return (
        <div className="session-monitor">
            <h2>Active Sessions</h2>
            <p>Currently active users and their session info will be shown here.</p>
        </div>
    );
};

export default SessionMonitor;