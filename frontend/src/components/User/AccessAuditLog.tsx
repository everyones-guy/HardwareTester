// src/components/User/AccessAuditLog.tsx
import React from "react";

const AccessAuditLog: React.FC = () => {
    return (
        <div className="access-audit-log">
            <h2>Audit Log</h2>
            <p>Recent logins, failed attempts, or actions will appear here.</p>
        </div>
    );
};

export default AccessAuditLog;